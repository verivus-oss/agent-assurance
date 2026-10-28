use std::io::Read;

// This reader accepts the single-disk ZIP32 records used by the ecosystem
// exports. It never creates paths or interprets links, permissions or code.
pub struct Member<'a> {
    pub name: &'a str,
    pub unix_mode: Option<u32>,
    size: u32,
    compressed: &'a [u8],
    method: u16,
    crc: u32,
}

pub struct Archive<'a> {
    pub members: Vec<Member<'a>>,
}

fn part(bytes: &[u8], start: usize, length: usize) -> Result<&[u8], String> {
    let end = start
        .checked_add(length)
        .ok_or("archive offset exceeds its bound")?;
    bytes
        .get(start..end)
        .ok_or_else(|| "archive field is truncated".into())
}

fn u16_at(bytes: &[u8], offset: usize) -> Result<u16, String> {
    Ok(u16::from_le_bytes(
        part(bytes, offset, 2)?
            .try_into()
            .map_err(|_| "invalid archive integer")?,
    ))
}

fn u32_at(bytes: &[u8], offset: usize) -> Result<u32, String> {
    Ok(u32::from_le_bytes(
        part(bytes, offset, 4)?
            .try_into()
            .map_err(|_| "invalid archive integer")?,
    ))
}

fn extra(bytes: &[u8]) -> Result<(), String> {
    let mut offset = 0;
    while offset < bytes.len() {
        let kind = u16_at(bytes, offset)?;
        let size = usize::from(u16_at(bytes, offset + 2)?);
        if kind == 1 {
            return Err("ZIP64 advisory archives are unsupported".into());
        }
        part(bytes, offset + 4, size)?;
        offset += 4 + size;
    }
    Ok(())
}

impl<'a> Archive<'a> {
    pub fn parse(bytes: &'a [u8]) -> Result<Self, String> {
        if bytes.len() < 22 {
            return Err("advisory archive end record is absent".into());
        }
        let first = bytes.len().saturating_sub(22 + 65535);
        let end = (first..=bytes.len() - 22)
            .rev()
            .find(|offset| bytes.get(*offset..*offset + 4) == Some(b"PK\x05\x06"))
            .ok_or("advisory archive end record is absent")?;
        if end + 22 + usize::from(u16_at(bytes, end + 20)?) != bytes.len()
            || u16_at(bytes, end + 4)? != 0
            || u16_at(bytes, end + 6)? != 0
        {
            return Err("advisory archive has trailing bytes or multiple disks".into());
        }
        let count = u16_at(bytes, end + 10)?;
        if count == 0 || count == u16::MAX || u16_at(bytes, end + 8)? != count {
            return Err(
                "advisory archive member population is absent, inconsistent or ZIP64".into(),
            );
        }
        let central_size = u32_at(bytes, end + 12)? as usize;
        let central_start = u32_at(bytes, end + 16)? as usize;
        if central_start.checked_add(central_size) != Some(end) {
            return Err("advisory central directory population differs".into());
        }
        let central = part(bytes, central_start, central_size)?;
        let mut offset = 0;
        let mut members = Vec::new();
        let mut spans = Vec::new();
        for _ in 0..count {
            let header = part(central, offset, 46)?;
            if &header[..4] != b"PK\x01\x02" {
                return Err("invalid advisory central record".into());
            }
            let flags = u16_at(header, 8)?;
            let method = u16_at(header, 10)?;
            let crc = u32_at(header, 16)?;
            let compressed_size = u32_at(header, 20)? as usize;
            let size = u32_at(header, 24)?;
            let name_size = usize::from(u16_at(header, 28)?);
            let extra_size = usize::from(u16_at(header, 30)?);
            let comment_size = usize::from(u16_at(header, 32)?);
            let attributes = u32_at(header, 38)?;
            let local_offset = u32_at(header, 42)? as usize;
            if flags & !0x080e != 0
                || !matches!(method, 0 | 8)
                || u16_at(header, 34)? != 0
                || compressed_size == u32::MAX as usize
                || size == u32::MAX
                || local_offset >= central_start
            {
                return Err("encrypted, multipart or unsupported advisory ZIP record".into());
            }
            let raw_name = part(central, offset + 46, name_size)?;
            if raw_name.is_empty() || (flags & 0x0800 == 0 && !raw_name.is_ascii()) {
                return Err("advisory archive member encoding is unsupported".into());
            }
            let name = std::str::from_utf8(raw_name)
                .map_err(|_| "advisory archive member is not UTF-8")?;
            extra(part(central, offset + 46 + name_size, extra_size)?)?;
            part(central, offset + 46 + name_size + extra_size, comment_size)?;
            offset += 46 + name_size + extra_size + comment_size;
            let local = part(bytes, local_offset, 30)?;
            if &local[..4] != b"PK\x03\x04"
                || u16_at(local, 6)? != flags
                || u16_at(local, 8)? != method
                || usize::from(u16_at(local, 26)?) != name_size
            {
                return Err("advisory local header differs from central record".into());
            }
            let local_extra = usize::from(u16_at(local, 28)?);
            if part(bytes, local_offset + 30, name_size)? != raw_name {
                return Err("advisory local name differs from central record".into());
            }
            extra(part(bytes, local_offset + 30 + name_size, local_extra)?)?;
            let local_values = (u32_at(local, 14)?, u32_at(local, 18)?, u32_at(local, 22)?);
            let declared = (crc, compressed_size as u32, size);
            let local_valid =
                local_values == declared || flags & 8 != 0 && local_values == (0, 0, 0);
            if !local_valid {
                return Err("advisory local sizes or CRC differ from central record".into());
            }
            let payload = local_offset + 30 + name_size + local_extra;
            let compressed = part(bytes, payload, compressed_size)?;
            let mut data_end = payload + compressed_size;
            if flags & 8 != 0 {
                if bytes.get(data_end..data_end + 4) == Some(b"PK\x07\x08") {
                    data_end += 4;
                }
                if (
                    u32_at(bytes, data_end)?,
                    u32_at(bytes, data_end + 4)?,
                    u32_at(bytes, data_end + 8)?,
                ) != declared
                {
                    return Err("advisory data descriptor differs from central record".into());
                }
                data_end += 12;
            }
            if data_end > central_start {
                return Err("advisory payload overlaps its directory".into());
            }
            spans.push((local_offset, data_end));
            let unix_mode = if header[5] == 3 {
                Some(attributes >> 16)
            } else {
                None
            };
            members.push(Member {
                name,
                unix_mode,
                size,
                compressed,
                method,
                crc,
            });
        }
        if offset != central.len() || members.len() != usize::from(count) {
            return Err("advisory central record population is incomplete".into());
        }
        spans.sort_unstable();
        let mut consumed = 0;
        for (start, end) in spans {
            if start != consumed || end <= start {
                return Err("advisory local records overlap or leave unaccounted bytes".into());
            }
            consumed = end;
        }
        if consumed != central_start {
            return Err("advisory local byte population is incomplete".into());
        }
        Ok(Self { members })
    }
}

impl Member<'_> {
    pub fn size(&self) -> u64 {
        u64::from(self.size)
    }

    pub fn read(&self, limit: u64) -> Result<Vec<u8>, String> {
        if u64::from(self.size) > limit {
            return Err("advisory member exceeds its bound".into());
        }
        let mut bytes = Vec::new();
        if self.method == 0 {
            if self.compressed.len() != self.size as usize {
                return Err("stored advisory member size differs".into());
            }
            bytes.extend_from_slice(self.compressed);
        } else {
            let mut decoder = flate2::read::DeflateDecoder::new(self.compressed);
            decoder
                .by_ref()
                .take(
                    limit
                        .checked_add(1)
                        .ok_or("invalid advisory expansion bound")?,
                )
                .read_to_end(&mut bytes)
                .map_err(|_| "advisory member integrity or decoding failed")?;
            if decoder.total_in() != self.compressed.len() as u64 {
                return Err("advisory compressed byte population differs".into());
            }
        }
        if bytes.len() != self.size as usize || crc32fast::hash(&bytes) != self.crc {
            return Err("advisory member integrity or decoding failed".into());
        }
        Ok(bytes)
    }
}

#[cfg(test)]
pub fn stored_fixture(files: &[(&str, &[u8])]) -> Vec<u8> {
    let mut bytes = Vec::new();
    let mut directory = Vec::new();
    for (name, data) in files {
        let offset = bytes.len() as u32;
        let size = data.len() as u32;
        let crc = crc32fast::hash(data);
        let mut header = vec![0; 30];
        header[..4].copy_from_slice(b"PK\x03\x04");
        header[4..6].copy_from_slice(&20u16.to_le_bytes());
        header[14..18].copy_from_slice(&crc.to_le_bytes());
        header[18..22].copy_from_slice(&size.to_le_bytes());
        header[22..26].copy_from_slice(&size.to_le_bytes());
        header[26..28].copy_from_slice(&(name.len() as u16).to_le_bytes());
        bytes.extend(header);
        bytes.extend(name.as_bytes());
        bytes.extend(*data);
        let mut central = vec![0; 46];
        central[..4].copy_from_slice(b"PK\x01\x02");
        central[4..6].copy_from_slice(&0x0314u16.to_le_bytes());
        central[6..8].copy_from_slice(&20u16.to_le_bytes());
        central[16..20].copy_from_slice(&crc.to_le_bytes());
        central[20..24].copy_from_slice(&size.to_le_bytes());
        central[24..28].copy_from_slice(&size.to_le_bytes());
        central[28..30].copy_from_slice(&(name.len() as u16).to_le_bytes());
        central[38..42].copy_from_slice(&(0o100644u32 << 16).to_le_bytes());
        central[42..46].copy_from_slice(&offset.to_le_bytes());
        directory.extend(central);
        directory.extend(name.as_bytes());
    }
    let start = bytes.len() as u32;
    let length = directory.len() as u32;
    bytes.extend(directory);
    let mut end = vec![0; 22];
    end[..4].copy_from_slice(b"PK\x05\x06");
    end[8..10].copy_from_slice(&(files.len() as u16).to_le_bytes());
    end[10..12].copy_from_slice(&(files.len() as u16).to_le_bytes());
    end[12..16].copy_from_slice(&length.to_le_bytes());
    end[16..20].copy_from_slice(&start.to_le_bytes());
    bytes.extend(end);
    bytes
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn independently_known_crc_and_deflate_bytes() {
        assert_eq!(crc32fast::hash(b"123456789"), 0xcbf43926);
        let member = Member {
            name: "CONTROL.json",
            unix_mode: Some(0o100644),
            size: 5,
            compressed: &[0xcb, 0x48, 0xcd, 0xc9, 0xc9, 0x07, 0x00],
            method: 8,
            crc: 0x3610a686,
        };
        assert_eq!(member.read(5).unwrap(), b"hello");
        assert!(member.read(4).is_err());
        let trailing = Member {
            compressed: &[0xcb, 0x48, 0xcd, 0xc9, 0xc9, 0x07, 0x00, 0],
            ..member
        };
        assert!(trailing.read(5).is_err());
    }

    #[test]
    fn complete_local_and_central_populations_are_required() {
        let bytes = stored_fixture(&[("CONTROL.json", b"123456789"), ("NEXT.json", b"next")]);
        let archive = Archive::parse(&bytes).unwrap();
        assert_eq!(archive.members.len(), 2);
        assert_eq!(archive.members[0].read(9).unwrap(), b"123456789");
        assert_eq!(archive.members[1].read(9).unwrap(), b"next");
        assert!(
            archive
                .members
                .iter()
                .all(|member| member.unix_mode == Some(0o100644))
        );
        for length in 0..bytes.len() {
            assert!(Archive::parse(&bytes[..length]).is_err());
        }
        let central = u32_at(&bytes, bytes.len() - 22 + 16).unwrap() as usize;
        let mut mutations = Vec::new();
        for (offset, value) in [
            (6, 1),
            (8, 99),
            (central + 8, 1),
            (central + 10, 99),
            (central + 34, 1),
            (central + 42, 1),
            (bytes.len() - 22 + 4, 1),
            (bytes.len() - 22 + 8, 1),
            (bytes.len() - 22 + 16, 1),
        ] {
            let mut bad = bytes.clone();
            bad[offset] = value;
            mutations.push(bad);
        }
        let mut trailing = bytes.clone();
        trailing.push(0);
        mutations.push(trailing);
        for bad in mutations {
            assert!(Archive::parse(&bad).is_err());
        }
        let mut corrupt = bytes.clone();
        corrupt[30 + "CONTROL.json".len()] = b'0';
        let archive = Archive::parse(&corrupt).unwrap();
        assert_eq!(
            archive.members[0].read(9).unwrap_err(),
            "advisory member integrity or decoding failed"
        );
    }

    #[test]
    fn descriptor_records_have_exact_sizes_and_crc() {
        let source = stored_fixture(&[("CONTROL.json", b"hello")]);
        let central = u32_at(&source, source.len() - 22 + 16).unwrap() as usize;
        let mut bytes = source[..central].to_vec();
        bytes[6..8].copy_from_slice(&8u16.to_le_bytes());
        let crc = crc32fast::hash(b"hello");
        bytes[14..26].fill(0);
        bytes.extend(b"PK\x07\x08");
        bytes.extend(crc.to_le_bytes());
        bytes.extend(5u32.to_le_bytes());
        bytes.extend(5u32.to_le_bytes());
        bytes.extend_from_slice(&source[central..]);
        bytes[central + 16 + 8..central + 16 + 10].copy_from_slice(&8u16.to_le_bytes());
        let end = bytes.len() - 22;
        bytes[end + 16..end + 20].copy_from_slice(&((central + 16) as u32).to_le_bytes());
        assert_eq!(
            Archive::parse(&bytes).unwrap().members[0].read(5).unwrap(),
            b"hello"
        );
        bytes[central + 4] ^= 1;
        assert!(Archive::parse(&bytes).is_err());
    }
}
