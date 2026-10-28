#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Scope {
    Text,
    PinnedDictionary,
    Excluded(&'static str),
}

pub fn classify(path: &str) -> Result<Scope, &'static str> {
    let parts: Vec<_> = path.split('/').collect();
    if path.is_empty()
        || std::path::Path::new(path).is_absolute()
        || parts
            .iter()
            .any(|part| matches!(*part, "" | "." | ".." | ".git"))
        || path.contains('\0')
    {
        return Err("spelling source identity must be a repository-relative path");
    }
    let basename = parts.last().ok_or("spelling source has no basename")?;
    if parts.len() > 2
        && (parts.starts_with(&["docs", "reviews"])
            || parts.starts_with(&["docs", "research"])
            || parts.starts_with(&["docs", "claim_analysis"]))
    {
        return Ok(Scope::Excluded("declared historical or research evidence"));
    }
    if parts.len() > 1 && parts[0] == ".local" {
        return Ok(Scope::Excluded("declared local working copies"));
    }
    if path == "tools/werner-style-policy.toml" {
        return Ok(Scope::Excluded("declared anti-pattern word data"));
    }
    if matches!(*basename, "Cargo.lock" | "go.sum" | "uv.lock") {
        return Ok(Scope::Excluded("declared dependency lock data"));
    }
    if parts.len() == 4
        && parts.starts_with(&["foundations", "ijb", "examples"])
        && (basename.starts_with("06-") || basename.starts_with("07-"))
        && basename.ends_with(".md")
    {
        return Ok(Scope::Excluded("declared canonical identifier examples"));
    }
    if path == "tools/dagtoml-spell/data/words.csv" {
        return Ok(Scope::PinnedDictionary);
    }
    Ok(Scope::Text)
}

pub fn binary_kind(path: &str, source: &[u8]) -> Option<&'static str> {
    let path = path.to_ascii_lowercase();
    if path.ends_with(".png") && source.starts_with(b"\x89PNG\r\n\x1a\n") {
        Some("declared PNG image signature; content is outside word checking")
    } else if path.ends_with(".ico")
        && source.len() >= 6
        && source.starts_with(&[0, 0, 1, 0])
        && u16::from_le_bytes([source[4], source[5]]) > 0
    {
        Some("declared ICO image signature; content is outside word checking")
    } else {
        None
    }
}

#[cfg(test)]
mod tests {
    use super::{Scope, binary_kind, classify};

    #[test]
    fn declared_scope_and_lookalikes() {
        let exclusions = [
            "docs/reviews/a.md",
            "docs/reviews/deep/a.py",
            "docs/research/a.md",
            "docs/claim_analysis/a.md",
            ".local/a.md",
            "tools/werner-style-policy.toml",
            "Cargo.lock",
            "tools/a/Cargo.lock",
            "a/go.sum",
            "a/uv.lock",
            "foundations/ijb/examples/06-a.md",
            "foundations/ijb/examples/07-a.md",
        ];
        for path in exclusions {
            assert!(
                matches!(classify(path).unwrap(), Scope::Excluded(_)),
                "declared scope changed: {path}"
            );
        }
        for path in [
            "spec.md",
            "core/ontology.toml",
            "profiles/a/PROFILE.toml",
            "validators/test_example.py",
            "tools/check/src/main.rs",
            "docs/reviews-extra/a.md",
            "docs/reviews",
            "docs/research",
            "docs/claim_analysis",
            "docs/research.md",
            ".local",
            ".local-extra/a",
            "tools/werner-style-policy.toml.md",
            "a/MyCargo.lock",
            "a/go.sum.md",
            "foundations/ijb/examples/deep/06-a.md",
            "foundations/ijb/examples/06-a.toml",
            "foundations/ijb/examples/08-a.md",
        ] {
            assert_eq!(
                classify(path).unwrap(),
                Scope::Text,
                "governed source was excluded: {path}"
            );
        }
        assert_eq!(
            classify("tools/dagtoml-spell/data/words.csv").unwrap(),
            Scope::PinnedDictionary
        );
        for path in [
            "",
            "/absolute",
            "../outside",
            "a/../outside",
            "./a",
            "a//b",
            "a/.git/config",
            "bad\0name",
        ] {
            assert!(
                classify(path).is_err(),
                "invalid source identity accepted: {path:?}"
            );
        }
    }

    #[test]
    fn binary_signatures_do_not_hide_text_or_code() {
        assert_eq!(
            binary_kind("image.png", b"\x89PNG\r\n\x1a\npayload"),
            Some("declared PNG image signature; content is outside word checking")
        );
        assert_eq!(
            binary_kind("image.ico", &[0, 0, 1, 0, 1, 0]),
            Some("declared ICO image signature; content is outside word checking")
        );
        for (path, source) in [
            ("image.png", b"ordinary source text".as_slice()),
            ("source.py", b"\x89PNG\r\n\x1a\n".as_slice()),
            ("image.ico", [0, 0, 1, 0, 0, 0].as_slice()),
            ("image.ico", [0, 0, 1, 0].as_slice()),
        ] {
            assert_eq!(binary_kind(path, source), None);
        }
    }
}
