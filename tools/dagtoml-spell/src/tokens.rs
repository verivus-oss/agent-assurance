// Adapted from crate-ci/typos, tokens.rs at
// 7f9d0819ca1c008ade73f4b41fa9d258d48f605b.
// Supplier licenses are retained beside this crate.
// The text parser uses the supplier's structured lexer. The unused byte
// input and ASCII optimization are retired; every conversion is checked.

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Identifier<'a> {
    pub text: &'a str,
    pub start: usize,
    pub end: usize,
}

pub fn identifiers(content: &str) -> Result<Vec<Identifier<'_>>, &'static str> {
    let mut input = content;
    let mut result = Vec::new();
    while !input.is_empty() {
        let before = input.len();
        match parser::next_identifier(&mut input) {
            Ok(text) => {
                if text.is_empty() || input.len() >= before {
                    return Err("spelling lexer did not make progress");
                }
                let start = (text.as_ptr() as usize)
                    .checked_sub(content.as_ptr() as usize)
                    .ok_or("spelling lexer returned an unrelated source")?;
                let end = start
                    .checked_add(text.len())
                    .ok_or("spelling lexer source span overflow")?;
                if content.get(start..end) != Some(text) {
                    return Err("spelling lexer returned an invalid source span");
                }
                if start < content.len() - before || end > content.len() - input.len() {
                    return Err("spelling lexer returned a source span outside its consumed input");
                }
                result.push(Identifier { text, start, end });
            }
            Err(_) if input.is_empty() => break,
            Err(_) => return Err("spelling lexer left unexamined source"),
        }
    }
    Ok(result)
}

mod parser {
    use winnow::Result;
    use winnow::combinator::trace;
    use winnow::combinator::{alt, eof, opt, peek, preceded, repeat, terminated};
    use winnow::error::ParserError;
    use winnow::prelude::*;
    use winnow::stream::AsBStr;
    use winnow::stream::AsChar;
    use winnow::stream::Compare;
    use winnow::stream::SliceLen;
    use winnow::stream::Stream;
    use winnow::stream::StreamIsPartial;
    use winnow::token::{one_of, take_while};

    /// Avoid worst-case parse times by limiting how much a `take_while` can take if something
    /// later may cause it to fail.
    const NON_TERMINATING_CAP: usize = 1024;

    pub(crate) fn next_identifier<'i, T>(input: &mut T) -> Result<<T as Stream>::Slice, ()>
    where
        T: Compare<&'i str>,
        T: Compare<char>,
        T: Stream + StreamIsPartial + PartialEq,
        <T as Stream>::Slice: AsBStr + SliceLen + Default,
        <T as Stream>::Token: AsChar + Copy,
    {
        preceded(ignore, identifier).parse_next(input)
    }

    fn identifier<T>(input: &mut T) -> Result<<T as Stream>::Slice, ()>
    where
        T: Stream + StreamIsPartial + PartialEq,
        <T as Stream>::Slice: AsBStr + SliceLen + Default,
        <T as Stream>::Token: AsChar + Copy,
    {
        // Generally a language would be `{XID_Start}{XID_Continue}*` but going with only
        // `{XID_Continue}+` because XID_Continue is a superset of XID_Start and rather catch odd
        // or unexpected cases than strip off start characters to a word since we aren't doing a
        // proper word boundary parse
        trace(
            "identifier",
            take_while(1.., is_xid_continue)
                .verify(|s: &<T as Stream>::Slice| std::str::from_utf8(s.as_bstr()).is_ok()),
        )
        .parse_next(input)
    }

    fn ignore<'i, T>(input: &mut T) -> Result<<T as Stream>::Slice, ()>
    where
        T: Compare<&'i str>,
        T: Compare<char>,
        T: Stream + StreamIsPartial + PartialEq,
        <T as Stream>::Slice: AsBStr + SliceLen + Default,
        <T as Stream>::Token: AsChar + Copy,
    {
        trace(
            "ignore",
            take_many0(alt((
                // CAUTION: If adding an ignorable literal, if it doesn't start with `is_xid_continue`,
                // - Update `is_ignore_char` to make sure `other` doesn't eat it all up
                // - Make sure you always consume it
                terminated(uuid_literal, sep1),
                terminated(email_literal, sep1),
                terminated(url_literal, sep1),
                terminated(jwt, sep1),
                terminated(ssh_ed25519_pub_key, sep1),
                terminated(base64_literal, sep1), // base64 should be quoted or something
                alt((
                    terminated(hash_literal, sep1),
                    terminated(ordinal_literal, sep1),
                    terminated(hex_literal, sep1),
                    terminated(dec_literal, sep1), // Allow digit-prefixed words
                    terminated(css_color, sep1),
                    terminated(c_escape, sep1),
                    terminated(printf, sep1),
                )),
                other,
            ))),
        )
        .parse_next(input)
    }

    fn sep1<T>(input: &mut T) -> Result<<T as Stream>::Slice, ()>
    where
        T: Stream + StreamIsPartial + PartialEq,
        <T as Stream>::Slice: AsBStr + SliceLen + Default,
        <T as Stream>::Token: AsChar + Copy,
    {
        alt((
            take_while(1.., is_ignore_char),
            peek(one_of(|c| !is_xid_continue(c))).take(),
            eof.map(|_| <T as Stream>::Slice::default()),
        ))
        .parse_next(input)
    }

    fn other<T>(input: &mut T) -> Result<<T as Stream>::Slice, ()>
    where
        T: Stream + StreamIsPartial + PartialEq,
        <T as Stream>::Slice: AsBStr + SliceLen + Default,
        <T as Stream>::Token: AsChar + Copy,
    {
        trace(
            "other",
            (
                one_of(|c| !is_xid_continue(c)),
                take_while(0.., is_ignore_char),
            )
                .take(),
        )
        .parse_next(input)
    }

    fn ordinal_literal<'i, T>(input: &mut T) -> Result<<T as Stream>::Slice, ()>
    where
        T: Compare<char>,
        T: Compare<&'i str>,
        T: Stream + StreamIsPartial + PartialEq,
        <T as Stream>::Slice: AsBStr + SliceLen + Default,
        <T as Stream>::Token: AsChar + Copy,
    {
        fn is_sep(c: impl AsChar) -> bool {
            let c = c.as_char();
            // Avoid markdown throwing off our ordinal detection
            ['_'].contains(&c)
        }

        trace(
            "ordinal_literal",
            (
                take_while(0.., is_sep),
                take_while(1.., is_dec_digit),
                alt((('s', 't'), ('n', 'd'), ('r', 'd'), ('t', 'h'))),
                take_while(0.., is_sep),
            )
                .take(),
        )
        .parse_next(input)
    }

    fn dec_literal<T>(input: &mut T) -> Result<<T as Stream>::Slice, ()>
    where
        T: Stream + StreamIsPartial + PartialEq,
        <T as Stream>::Slice: AsBStr + SliceLen + Default,
        <T as Stream>::Token: AsChar + Copy,
    {
        trace("dec_literal", take_while(1.., is_dec_digit_with_sep)).parse_next(input)
    }

    fn hex_literal<T>(input: &mut T) -> Result<<T as Stream>::Slice, ()>
    where
        T: Compare<char>,
        T: Stream + StreamIsPartial + PartialEq,
        <T as Stream>::Slice: AsBStr + SliceLen + Default,
        <T as Stream>::Token: AsChar + Copy,
    {
        (
            '0',
            alt(('x', 'X')),
            take_while(1.., is_hex_digit_with_sep),
            take_while(0.., is_xid_continue)
                .verify(|s: &<T as Stream>::Slice| std::str::from_utf8(s.as_bstr()).is_ok()),
        )
            .take()
            .parse_next(input)
    }

    fn css_color<T>(input: &mut T) -> Result<<T as Stream>::Slice, ()>
    where
        T: Compare<char>,
        T: Stream + StreamIsPartial + PartialEq,
        <T as Stream>::Slice: AsBStr + SliceLen + Default,
        <T as Stream>::Token: AsChar + Copy,
    {
        trace(
            "color",
            (
                '#',
                alt((
                    (take_while(3..=8, is_lower_hex_digit), peek(sep1)),
                    (take_while(3..=8, is_upper_hex_digit), peek(sep1)),
                )),
            )
                .take(),
        )
        .parse_next(input)
    }

    fn jwt<'i, T>(input: &mut T) -> Result<<T as Stream>::Slice, ()>
    where
        T: Compare<char>,
        T: Compare<&'i str>,
        T: Stream + StreamIsPartial + PartialEq,
        <T as Stream>::Slice: AsBStr + SliceLen + Default,
        <T as Stream>::Token: AsChar + Copy,
    {
        trace(
            "jwt",
            (
                "ey",
                take_while(20.., is_jwt_token),
                ".ey",
                take_while(20.., is_jwt_token),
                '.',
                take_while(20.., is_jwt_token),
            )
                .take(),
        )
        .parse_next(input)
    }

    #[inline]
    fn is_jwt_token(i: impl AsChar + Copy) -> bool {
        let c = i.as_char();
        c.is_ascii_lowercase()
            || c.is_ascii_uppercase()
            || c.is_ascii_digit()
            || c == '_'
            || c == '-'
    }

    fn ssh_ed25519_pub_key<'i, T>(input: &mut T) -> Result<<T as Stream>::Slice, ()>
    where
        T: Compare<char>,
        T: Compare<&'i str>,
        T: Stream + StreamIsPartial + PartialEq,
        <T as Stream>::Slice: AsBStr + SliceLen + Default,
        <T as Stream>::Token: AsChar + Copy,
    {
        trace(
            "ssh_ed25519_pub_key",
            (
                "AAAAC3NzaC1lZDI1NTE5AAAAI",
                // The supplier lexer accepts a wider alphabet than the protocol's A through P.
                take_while(43, is_base64_digit),
            )
                .take(),
        )
        .parse_next(input)
    }

    fn uuid_literal<T>(input: &mut T) -> Result<<T as Stream>::Slice, ()>
    where
        T: Compare<char>,
        T: Stream + StreamIsPartial + PartialEq,
        <T as Stream>::Slice: AsBStr + SliceLen + Default,
        <T as Stream>::Token: AsChar + Copy,
    {
        trace(
            "uuid",
            alt((
                (
                    take_while(8, is_lower_hex_digit),
                    '-',
                    take_while(4, is_lower_hex_digit),
                    '-',
                    take_while(4, is_lower_hex_digit),
                    '-',
                    take_while(4, is_lower_hex_digit),
                    '-',
                    take_while(12, is_lower_hex_digit),
                ),
                (
                    take_while(8, is_upper_hex_digit),
                    '-',
                    take_while(4, is_upper_hex_digit),
                    '-',
                    take_while(4, is_upper_hex_digit),
                    '-',
                    take_while(4, is_upper_hex_digit),
                    '-',
                    take_while(12, is_upper_hex_digit),
                ),
            ))
            .take(),
        )
        .parse_next(input)
    }

    fn hash_literal<T>(input: &mut T) -> Result<<T as Stream>::Slice, ()>
    where
        T: Stream + StreamIsPartial + PartialEq,
        <T as Stream>::Slice: AsBStr + SliceLen + Default,
        <T as Stream>::Token: AsChar + Copy,
    {
        // Size considerations:
        //   - 40 characters holds for a SHA-1 hash from older Git versions.
        //   - 64 characters holds for a SHA-256 hash from newer Git versions.
        //   - Git allows abbreviated hashes, but we need a good abbreviation
        //     that won't be mistaken for a variable name.
        //   - Through experimentation we've found that there is almost
        //     never any actual text inside a hex string of 32 characters
        //     or more.

        const IGNORE_HEX_MIN: usize = 32;
        trace(
            "hash",
            alt((
                take_while(IGNORE_HEX_MIN.., is_lower_hex_digit),
                take_while(IGNORE_HEX_MIN.., is_upper_hex_digit),
            )),
        )
        .parse_next(input)
    }

    fn base64_literal<T>(input: &mut T) -> Result<<T as Stream>::Slice, ()>
    where
        T: Stream + StreamIsPartial + PartialEq,
        <T as Stream>::Slice: AsBStr + SliceLen + Default,
        <T as Stream>::Token: AsChar + Copy,
    {
        trace("base64", move |input: &mut T| {
            let start = input.checkpoint();
            let captured = take_while(1.., is_base64_digit).parse_next(input)?;

            const CHUNK: usize = 4;
            let padding_offset = input.offset_from(&start);
            let mut padding_len = CHUNK - padding_offset % CHUNK;
            if padding_len == CHUNK {
                padding_len = 0;
            }

            if captured.slice_len() < 90
                && padding_len == 0
                && captured.as_bstr().iter().all(|c| !b"/+".contains(c))
            {
                return Err(());
            }

            take_while(padding_len..=padding_len, is_base64_padding).parse_next(input)?;

            let after_offset = input.offset_from(&start);
            input.reset(&start);
            Ok(input.next_slice(after_offset))
        })
        .parse_next(input)
    }

    fn email_literal<T>(input: &mut T) -> Result<<T as Stream>::Slice, ()>
    where
        T: Compare<char>,
        T: Stream + StreamIsPartial + PartialEq,
        <T as Stream>::Slice: AsBStr + SliceLen + Default,
        <T as Stream>::Token: AsChar + Copy,
    {
        trace(
            "email",
            (
                take_while(1..NON_TERMINATING_CAP, is_localport_char),
                '@',
                take_while(1.., is_domain_char),
            )
                .take(),
        )
        .parse_next(input)
    }

    fn url_literal<'i, T>(input: &mut T) -> Result<<T as Stream>::Slice, ()>
    where
        T: Compare<char>,
        T: Compare<&'i str>,
        T: Stream + StreamIsPartial + PartialEq,
        <T as Stream>::Slice: AsBStr + SliceLen + Default,
        <T as Stream>::Token: AsChar + Copy,
    {
        trace(
            "url",
            (
                opt((
                    take_while(1..NON_TERMINATING_CAP, is_scheme_char),
                    // HACK: Technically you can skip `//` if you don't have a domain but that would
                    // get messy to support.
                    ("://"),
                )),
                (
                    opt((url_userinfo, '@')),
                    take_while(1..NON_TERMINATING_CAP, is_domain_char),
                    opt((
                        ':',
                        take_while(1..NON_TERMINATING_CAP, AsChar::is_dec_digit),
                    )),
                ),
                '/',
                // HACK: Too lazy to enumerate
                take_while(0.., is_path_query_fragment),
            )
                .take(),
        )
        .parse_next(input)
    }

    fn url_userinfo<T>(input: &mut T) -> Result<<T as Stream>::Slice, ()>
    where
        T: Compare<char>,
        T: Stream + StreamIsPartial + PartialEq,
        <T as Stream>::Slice: AsBStr + SliceLen + Default,
        <T as Stream>::Token: AsChar + Copy,
    {
        trace(
            "userinfo",
            (
                take_while(1..NON_TERMINATING_CAP, is_localport_char),
                opt((':', take_while(0..NON_TERMINATING_CAP, is_localport_char))),
            )
                .take(),
        )
        .parse_next(input)
    }

    fn c_escape<T>(input: &mut T) -> Result<<T as Stream>::Slice, ()>
    where
        T: Stream + StreamIsPartial + PartialEq,
        <T as Stream>::Slice: AsBStr + SliceLen + Default,
        <T as Stream>::Token: AsChar + Copy,
    {
        // We don't know whether the string we are parsing is a literal string (no escaping) or
        // regular string that does escaping. The escaped letter might be part of a word, or it
        // might not be. Rather than guess and be wrong part of the time and correct people's words
        // incorrectly, we opt for just not evaluating it at all.
        trace(
            "escape",
            (
                take_while(1..NON_TERMINATING_CAP, is_escape),
                take_while(0.., is_xid_continue),
            )
                .take(),
        )
        .parse_next(input)
    }

    fn printf<T>(input: &mut T) -> Result<<T as Stream>::Slice, ()>
    where
        T: Compare<char>,
        T: Stream + StreamIsPartial + PartialEq,
        <T as Stream>::Slice: AsBStr + SliceLen + Default,
        <T as Stream>::Token: AsChar + Copy,
    {
        trace("printf", ('%', take_while(1.., is_xid_continue)).take()).parse_next(input)
    }

    fn take_many0<I, E, F>(mut f: F) -> impl Parser<I, <I as Stream>::Slice, E>
    where
        I: Stream,
        F: Parser<I, <I as Stream>::Slice, E>,
        E: ParserError<I>,
    {
        move |i: &mut I| repeat(0.., f.by_ref()).map(|()| ()).take().parse_next(i)
    }

    #[inline]
    fn is_dec_digit(i: impl AsChar + Copy) -> bool {
        i.is_dec_digit()
    }

    #[inline]
    fn is_dec_digit_with_sep(i: impl AsChar + Copy) -> bool {
        i.is_dec_digit() || is_digit_sep(i.as_char())
    }

    #[inline]
    fn is_hex_digit_with_sep(i: impl AsChar + Copy) -> bool {
        i.is_hex_digit() || is_digit_sep(i.as_char())
    }

    #[inline]
    fn is_lower_hex_digit(i: impl AsChar + Copy) -> bool {
        let c = i.as_char();
        ('a'..='f').contains(&c) || c.is_ascii_digit()
    }

    #[inline]
    fn is_upper_hex_digit(i: impl AsChar + Copy) -> bool {
        let c = i.as_char();
        ('A'..='F').contains(&c) || c.is_ascii_digit()
    }

    #[inline]
    fn is_base64_digit(i: impl AsChar + Copy) -> bool {
        let c = i.as_char();
        c.is_ascii_lowercase()
            || c.is_ascii_uppercase()
            || c.is_ascii_digit()
            || c == '+'
            || c == '/'
    }

    #[inline]
    fn is_base64_padding(i: impl AsChar + Copy) -> bool {
        let c = i.as_char();
        c == '='
    }

    #[inline]
    fn is_localport_char(i: impl AsChar + Copy) -> bool {
        let c = i.as_char();
        c.is_ascii_lowercase()
            || c.is_ascii_uppercase()
            || c.is_ascii_digit()
            || "!#$%&'*+-/=?^_`{|}~().".find(c).is_some()
    }

    #[inline]
    fn is_domain_char(i: impl AsChar + Copy) -> bool {
        let c = i.as_char();
        c.is_ascii_lowercase()
            || c.is_ascii_uppercase()
            || c.is_ascii_digit()
            || "-().".find(c).is_some()
    }

    #[inline]
    fn is_path_query_fragment(i: impl AsChar + Copy) -> bool {
        let c = i.as_char();
        is_pchar(c) || "/?#".find(c).is_some()
    }

    #[inline]
    fn is_pchar(i: impl AsChar + Copy) -> bool {
        let c = i.as_char();
        is_uri_unreserved(c) || is_uri_sub_delims(c) || "%:@".find(c).is_some()
    }

    #[inline]
    fn is_uri_unreserved(i: impl AsChar + Copy) -> bool {
        let c = i.as_char();
        c.is_ascii_lowercase()
            || c.is_ascii_uppercase()
            || c.is_ascii_digit()
            || "-._~".find(c).is_some()
    }

    #[inline]
    fn is_uri_sub_delims(i: impl AsChar + Copy) -> bool {
        let c = i.as_char();
        "!$&'()*+,;=".find(c).is_some()
    }

    #[inline]
    fn is_scheme_char(i: impl AsChar + Copy) -> bool {
        let c = i.as_char();
        c.is_ascii_lowercase() || c.is_ascii_digit() || "+.-".find(c).is_some()
    }

    #[inline]
    fn is_ignore_char(i: impl AsChar + Copy) -> bool {
        let c = i.as_char();
        !unicode_ident::is_xid_continue(c) &&
            // See `c_escape`
            c != '\\' &&
            // See `printf`
            c != '%' &&
            // See `css_color`
            c != '#'
    }

    #[inline]
    fn is_xid_continue(i: impl AsChar + Copy) -> bool {
        let c = i.as_char();
        unicode_ident::is_xid_continue(c)
    }

    #[inline]
    fn is_escape(i: impl AsChar + Copy) -> bool {
        let c = i.as_char();
        c == '\\'
    }

    #[inline]
    fn is_digit_sep(chr: char) -> bool {
        // `_`: number literal separator in Rust and other languages
        // `'`: number literal separator in C++
        chr == '_' || chr == '\''
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, serde::Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum Case {
    Lower,
    Upper,
    Title,
    None,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Word<'a> {
    pub text: &'a str,
    pub start: usize,
    pub end: usize,
    pub case: Case,
}

#[derive(Clone, Copy, PartialEq, Eq)]
enum Mode {
    Lower,
    Upper,
    Number,
    Boundary,
}

impl Mode {
    fn of(character: char) -> Self {
        if character.is_lowercase() {
            Self::Lower
        } else if character.is_uppercase() {
            Self::Upper
        } else if character.is_ascii_digit() {
            Self::Number
        } else {
            Self::Boundary
        }
    }

    fn case(self, last: Self) -> Result<Case, &'static str> {
        match (self, last) {
            (Self::Upper, Self::Upper) => Ok(Case::Upper),
            (Self::Upper, Self::Lower) => Ok(Case::Title),
            (Self::Lower, Self::Lower) => Ok(Case::Lower),
            (Self::Number, Self::Number) => Ok(Case::None),
            _ => Err("spelling word state did not describe a complete case"),
        }
    }
}

pub fn words(identifier: Identifier<'_>) -> Result<Vec<Word<'_>>, &'static str> {
    if identifier.text.is_empty()
        || identifier.start.checked_add(identifier.text.len()) != Some(identifier.end)
    {
        return Err("spelling identifier has an invalid source interval");
    }
    let mut characters = identifier.text.char_indices().peekable();
    let mut start = 0;
    let mut first = Mode::Boundary;
    let mut last = Mode::Boundary;
    let mut result = Vec::new();
    let mut add = |start: usize, end: usize, case: Case| {
        result.push(Word {
            text: &identifier.text[start..end],
            start: identifier.start + start,
            end: identifier.start + end,
            case,
        });
    };
    while let Some((position, character)) = characters.next() {
        let current = Mode::of(character);
        if current == Mode::Boundary {
            if first != Mode::Boundary {
                return Err("spelling word boundary did not close its preceding word");
            }
            continue;
        }
        if first == Mode::Boundary {
            first = current;
            start = position;
        }
        if let Some(&(next_position, next)) = characters.peek() {
            let next_mode = Mode::of(next);
            match (last, current, next_mode) {
                (_, _, Mode::Boundary)
                | (_, Mode::Lower, Mode::Number)
                | (_, Mode::Upper, Mode::Number)
                | (_, Mode::Number, Mode::Lower)
                | (_, Mode::Number, Mode::Upper)
                | (_, Mode::Lower, Mode::Upper) => {
                    add(start, next_position, first.case(current)?);
                    start = next_position;
                    first = Mode::Boundary;
                    last = Mode::Boundary;
                }
                (Mode::Upper, Mode::Upper, Mode::Lower) => {
                    add(start, position, Case::Upper);
                    start = position;
                    first = current;
                    last = Mode::Boundary;
                }
                _ => last = current,
            }
        } else {
            add(start, identifier.text.len(), first.case(current)?);
        }
    }
    Ok(result)
}

#[cfg(test)]
mod tests {
    use super::{Case, Identifier, Mode, identifiers, words};

    #[test]
    fn declared_words_and_byte_spans() {
        let source = "HTTPServer getURLValue snake_case getProtocolAddress café12Name";
        let identifiers = identifiers(source).unwrap();
        let actual: Vec<_> = identifiers
            .into_iter()
            .flat_map(|identifier| words(identifier).unwrap())
            .collect();
        let expected = [
            ("HTTP", Case::Upper),
            ("Server", Case::Title),
            ("get", Case::Lower),
            ("URL", Case::Upper),
            ("Value", Case::Title),
            ("snake", Case::Lower),
            ("case", Case::Lower),
            ("get", Case::Lower),
            ("Protocol", Case::Title),
            ("Address", Case::Title),
            ("café", Case::Lower),
            ("12", Case::None),
            ("Name", Case::Title),
        ];
        assert_eq!(actual.len(), expected.len());
        for (word, (text, case)) in actual.iter().zip(expected) {
            assert_eq!(word.text, text);
            assert_eq!(word.case, case);
            assert_eq!(source.get(word.start..word.end), Some(text));
        }
    }

    #[test]
    fn literals_do_not_become_dictionary_words() {
        let values = [
            "https://example.invalid/recieve",
            "contact@example.invalid",
            "2d82f493-51a6-4e87-9b01-5d3e8f41b20c",
            "0123456789abcdef0123456789abcdef01234567",
            "0x12345678",
            "#FF00AA",
            "1st",
            "\\n",
            "%08x",
        ];
        for value in values {
            assert!(
                identifiers(value).unwrap().is_empty(),
                "literal reached dictionary words: {value:?}"
            );
        }
        assert_eq!(identifiers("receive").unwrap().len(), 1);
        assert!(identifiers("").unwrap().is_empty());
        for value in [
            "AAAA+AAA".to_owned(),
            "G".repeat(92),
            format!("{}=", "G".repeat(91)),
        ] {
            assert!(
                identifiers(&value).unwrap().is_empty(),
                "declared encoding literal reached word lookup"
            );
        }
        assert!(!identifiers(&"G".repeat(91)).unwrap().is_empty());
        assert!(!identifiers("AAAA-AAA").unwrap().is_empty());
    }

    #[test]
    fn case_state_population_and_invalid_identity() {
        let modes = [Mode::Lower, Mode::Upper, Mode::Number, Mode::Boundary];
        let mut visited = 0;
        for (a, first) in modes.iter().enumerate() {
            for (b, last) in modes.iter().enumerate() {
                let expected = match (a, b) {
                    (0, 0) => Some(Case::Lower),
                    (1, 0) => Some(Case::Title),
                    (1, 1) => Some(Case::Upper),
                    (2, 2) => Some(Case::None),
                    _ => None,
                };
                assert_eq!(first.case(*last).ok(), expected);
                visited += 1;
            }
        }
        assert_eq!(visited, modes.len() * modes.len());
        for identifier in [
            Identifier {
                text: "",
                start: 0,
                end: 0,
            },
            Identifier {
                text: "word",
                start: usize::MAX,
                end: 3,
            },
            Identifier {
                text: "word",
                start: 0,
                end: 3,
            },
        ] {
            assert!(words(identifier).is_err());
        }
    }
}
