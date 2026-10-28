use std::collections::BTreeSet;
use std::ops::Range;

use crate::digest::sha256;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Container {
    Tuple,
    FrozenSet,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Table {
    pub binding: String,
    pub container: Container,
    pub values: Vec<String>,
    pub spans: Vec<Range<usize>>,
}

impl Table {
    pub fn digest(&self) -> Result<String, &'static str> {
        let mut values: Vec<_> = self.values.iter().map(String::as_bytes).collect();
        if self.container == Container::FrozenSet {
            values.sort();
        }
        let mut framed = b"spelling-python-byte-table-v1\0".to_vec();
        framed.push(match self.container {
            Container::Tuple => 1,
            Container::FrozenSet => 2,
        });
        for value in values {
            let size =
                u64::try_from(value.len()).map_err(|_| "spelling data operand is too large")?;
            framed.extend_from_slice(&size.to_be_bytes());
            framed.extend_from_slice(value);
        }
        Ok(sha256(&framed))
    }
}

struct Quoted {
    end: usize,
    body: Range<usize>,
}

fn quoted(source: &[u8], quote: usize) -> Result<Quoted, &'static str> {
    let marker = *source
        .get(quote)
        .ok_or("spelling data string opener is absent")?;
    if marker != b'\'' && marker != b'"' {
        return Err("spelling data string has no quote delimiter");
    }
    let width = if source.get(quote..quote + 3) == Some([marker; 3].as_slice()) {
        3
    } else {
        1
    };
    let start = quote + width;
    let mut position = start;
    while position < source.len() {
        if source[position] == b'\\' {
            position = position
                .checked_add(2)
                .ok_or("spelling string offset overflow")?;
        } else if source
            .get(position..position + width)
            .is_some_and(|slice| slice.iter().all(|byte| *byte == marker))
        {
            return Ok(Quoted {
                end: position + width,
                body: start..position,
            });
        } else if width == 1 && matches!(source[position], b'\r' | b'\n') {
            return Err("spelling data encountered an unterminated single string");
        } else {
            position += 1;
        }
    }
    Err("spelling data encountered an unterminated string")
}

fn spacing(source: &[u8], mut position: usize) -> usize {
    loop {
        while position < source.len() && source[position].is_ascii_whitespace() {
            position += 1;
        }
        if source.get(position) != Some(&b'#') {
            return position;
        }
        while position < source.len() && source[position] != b'\n' {
            position += 1;
        }
    }
}

fn identifier_byte(byte: u8) -> bool {
    byte.is_ascii_alphanumeric() || byte == b'_'
}

fn byte_prefix(prefix: &[u8]) -> bool {
    prefix.eq_ignore_ascii_case(b"b")
        || prefix.eq_ignore_ascii_case(b"br")
        || prefix.eq_ignore_ascii_case(b"rb")
}

fn parse_table(
    source: &[u8],
    binding: &str,
    mut position: usize,
    container: Container,
) -> Result<Table, &'static str> {
    position = spacing(source, position);
    if source.get(position) != Some(&b'=') || source.get(position + 1) == Some(&b'=') {
        return Err("spelling data binding must be an explicit assignment");
    }
    position = spacing(source, position + 1);
    if container == Container::FrozenSet {
        if !source[position..].starts_with(b"frozenset") {
            return Err("spelling data requires the declared frozen-set constructor");
        }
        position = spacing(source, position + b"frozenset".len());
        if source.get(position) != Some(&b'(') {
            return Err("spelling frozen-set call is absent");
        }
        position = spacing(source, position + 1);
    }
    if source.get(position) != Some(&b'(') {
        return Err("spelling byte data requires a literal tuple");
    }
    position += 1;
    let mut values = Vec::new();
    let mut spans = Vec::new();
    let mut unique = BTreeSet::new();
    loop {
        position = spacing(source, position);
        if source.get(position) == Some(&b')') {
            position += 1;
            if container == Container::FrozenSet {
                position = spacing(source, position);
                if source.get(position) != Some(&b')') {
                    return Err("spelling frozen-set call did not close");
                }
                position += 1;
            }
            while matches!(source.get(position), Some(b' ' | b'\t')) {
                position += 1;
            }
            if !matches!(source.get(position), None | Some(b'\r' | b'\n' | b'#')) {
                return Err("spelling byte-data binding has a nonliteral continuation");
            }
            if values.is_empty() {
                return Err("spelling byte-data table is absent");
            }
            return Ok(Table {
                binding: binding.to_owned(),
                container,
                values,
                spans,
            });
        }
        let start = position;
        while source
            .get(position)
            .is_some_and(|byte| byte.is_ascii_alphabetic())
        {
            position += 1;
        }
        if !byte_prefix(&source[start..position]) {
            return Err("spelling data table must contain only literal byte operands");
        }
        let value = quoted(source, position)?;
        let body = &source[value.body.clone()];
        if body.is_empty() || !body.is_ascii() || body.contains(&b'\\') {
            return Err("spelling byte data requires nonempty unescaped ASCII literals");
        }
        let text = std::str::from_utf8(body)
            .map_err(|_| "spelling byte data is not UTF-8")?
            .to_owned();
        if !unique.insert(text.clone()) {
            return Err("spelling byte data repeats an operand");
        }
        values.push(text);
        spans.push(start..value.end);
        position = spacing(source, value.end);
        if source.get(position) != Some(&b',') {
            if source.get(position) == Some(&b')') && values.len() > 1 {
                continue;
            }
            return Err("spelling byte-data tuple requires explicit item separators");
        }
        position += 1;
    }
}

pub fn python_table(
    source: &str,
    binding: &str,
    container: Container,
) -> Result<Table, &'static str> {
    if !binding
        .as_bytes()
        .first()
        .is_some_and(|byte| byte.is_ascii_alphabetic() || *byte == b'_')
        || !binding.bytes().all(identifier_byte)
    {
        return Err("spelling byte data requires a named binding");
    }
    let bytes = source.as_bytes();
    let mut position = 0;
    let mut found = None;
    while position < bytes.len() {
        match bytes[position] {
            b'#' => {
                while position < bytes.len() && bytes[position] != b'\n' {
                    position += 1;
                }
            }
            b'\'' | b'"' => position = quoted(bytes, position)?.end,
            byte if identifier_byte(byte) => {
                let start = position;
                while position < bytes.len() && identifier_byte(bytes[position]) {
                    position += 1;
                }
                if &bytes[start..position] == binding.as_bytes()
                    && (start == 0 || bytes[start - 1] == b'\n')
                {
                    if found.is_some() {
                        return Err("spelling byte-data binding is repeated");
                    }
                    found = Some(parse_table(bytes, binding, position, container)?);
                }
            }
            _ => position += 1,
        }
    }
    found.ok_or("spelling byte-data binding is absent")
}

pub fn python_byte_literals(
    source: &str,
    allowed: &[String],
) -> Result<Vec<Range<usize>>, &'static str> {
    let requested: BTreeSet<_> = allowed.iter().collect();
    if allowed.is_empty()
        || requested.len() != allowed.len()
        || allowed
            .iter()
            .any(|value| value.is_empty() || !value.is_ascii() || value.as_bytes().contains(&b'\\'))
    {
        return Err("spelling byte literal roles must name distinct nonempty ASCII values");
    }
    let bytes = source.as_bytes();
    let mut position = 0;
    let mut spans = Vec::new();
    let mut found = BTreeSet::new();
    while position < bytes.len() {
        match bytes[position] {
            b'#' => {
                while position < bytes.len() && bytes[position] != b'\n' {
                    position += 1;
                }
            }
            b'\'' | b'"' => position = quoted(bytes, position)?.end,
            byte if identifier_byte(byte) => {
                let start = position;
                while position < bytes.len() && identifier_byte(bytes[position]) {
                    position += 1;
                }
                if byte_prefix(&bytes[start..position])
                    && matches!(bytes.get(position), Some(b'\'' | b'"'))
                {
                    let value = quoted(bytes, position)?;
                    for item in allowed {
                        if item.as_bytes() == &bytes[value.body.clone()] {
                            spans.push(start..value.end);
                            found.insert(item);
                        }
                    }
                    position = value.end;
                }
            }
            _ => position += 1,
        }
    }
    if found != requested {
        return Err("spelling byte literal role has no matching source operand");
    }
    Ok(spans)
}

pub fn contains(spans: &[Range<usize>], start: usize, end: usize) -> bool {
    start < end
        && spans
            .iter()
            .any(|span| span.start <= start && end <= span.end)
}

#[cfg(test)]
mod tests {
    use super::{Container, contains, python_byte_literals, python_table};

    #[test]
    fn typed_tables_preserve_adjacent_prose() {
        let source = "# DATA = (b'comment',)\n\"\"\"DATA = (b'document',)\"\"\"\nDATA = (b'alpha', # adjacent prose\n b\"beta\",)\noutside = 'ordinary prose'\n";
        let table = python_table(source, "DATA", Container::Tuple).unwrap();
        assert_eq!(table.values, ["alpha", "beta"]);
        assert_eq!(table.spans.len(), table.values.len());
        for text in ["alpha", "beta"] {
            let start = source.find(text).unwrap();
            assert!(contains(&table.spans, start, start + text.len()));
        }
        for text in ["comment", "document", "adjacent", "ordinary"] {
            let start = source.find(text).unwrap();
            assert!(!contains(&table.spans, start, start + text.len()));
        }
        let frozen = python_table(
            "DATA = frozenset((b'beta', b'alpha',))\n",
            "DATA",
            Container::FrozenSet,
        )
        .unwrap();
        let reordered = python_table(
            "DATA = frozenset((b'alpha', b'beta',))\n",
            "DATA",
            Container::FrozenSet,
        )
        .unwrap();
        assert_eq!(frozen.digest().unwrap(), reordered.digest().unwrap());
        assert_ne!(table.digest().unwrap(), frozen.digest().unwrap());
        assert_eq!(
            python_table("DATA = (b'alpha', b'beta')\n", "DATA", Container::Tuple)
                .unwrap()
                .values,
            ["alpha", "beta"]
        );
        let continued = python_table(
            "DATA = frozenset((b'alpha',) # prose outside values\n)\n",
            "DATA",
            Container::FrozenSet,
        )
        .unwrap();
        assert_eq!(continued.values, ["alpha"]);
    }

    #[test]
    fn unsupported_or_missing_tables_fail() {
        for source in [
            "",
            "OTHER_DATA = (b'alpha',)\n",
            "DATA = ()\n",
            "DATA = ('alpha',)\n",
            "DATA = (b'alpha', b'alpha',)\n",
            "DATA = (b'alpha')\n",
            "DATA = (b'',)\n",
            "DATA = (b'alpha' + b'beta',)\n",
            "DATA = (b'alpha',)\nDATA = (b'beta',)\n",
            "DATA = (b'alpha,\n",
            "DATA = (b'escape\\n',)\n",
            "DATA = (b'alpha',) + other\n",
            "DATA = (b'alpha',)[:1]\n",
            "DATA = (b'alpha',).other\n",
        ] {
            assert!(
                python_table(source, "DATA", Container::Tuple).is_err(),
                "unsupported table accepted: {source:?}"
            );
        }
        assert!(python_table("DATA = (b'alpha',)\n", "DATA", Container::FrozenSet).is_err());
        for binding in ["", "1DATA", "OTHER_DATA"] {
            assert!(python_table("DATA = (b'alpha',)\n", binding, Container::Tuple).is_err());
        }
    }

    #[test]
    fn byte_literals_do_not_exempt_comments_or_ordinary_strings() {
        let source = "# b'fixed1_'\nordinary = \"b'fixed1_'\"\nvalue = b'fixed1_'\nother = b'fixed1_extra'\n";
        let spans = python_byte_literals(source, &["fixed1_".to_owned()]).unwrap();
        assert_eq!(spans.len(), 1);
        let start = source.find("value = ").unwrap() + "value = ".len();
        assert_eq!(spans[0], start..start + "b'fixed1_'".len());
        assert!(!contains(&spans, start - 1, spans[0].end));
        assert!(!contains(&spans, start, spans[0].end + 1));
        assert!(python_byte_literals("# b'fixed1_'\n", &["fixed1_".to_owned()]).is_err());
        assert!(python_byte_literals(source, &[]).is_err());
        assert!(
            python_byte_literals(source, &["fixed1_".to_owned(), "missing".to_owned()]).is_err()
        );
        assert!(
            python_byte_literals(source, &["fixed1_".to_owned(), "fixed1_".to_owned()]).is_err()
        );
    }
}
