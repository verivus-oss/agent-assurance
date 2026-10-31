namespace duckdb_re2 {
[[noreturn]] static void RefusePatternExecution() {
 throw std::runtime_error("pattern execution is retired in the DAG-TOML database driver");
}
class Regexp {
public:
 enum ParseFlags { FoldCase = 1, OneLine = 1 << 12 };
 int op() const { RefusePatternExecution(); }
 int parse_flags() const { RefusePatternExecution(); }
 int nsub() const { RefusePatternExecution(); }
 Regexp **sub() const { RefusePatternExecution(); }
 int nrunes() const { RefusePatternExecution(); }
 int *runes() const { RefusePatternExecution(); }
 int rune() const { RefusePatternExecution(); }
};
enum RegexpOp { kRegexpNoMatch=1, kRegexpEmptyMatch, kRegexpLiteral, kRegexpLiteralString,
 kRegexpConcat, kRegexpAlternate, kRegexpStar, kRegexpPlus, kRegexpQuest, kRegexpRepeat,
 kRegexpCapture, kRegexpAnyChar, kRegexpAnyByte, kRegexpBeginLine, kRegexpEndLine,
 kRegexpWordBoundary, kRegexpNoWordBoundary, kRegexpBeginText, kRegexpEndText,
 kRegexpCharClass, kRegexpHaveMatch };
RE2::RE2(const char *) { RefusePatternExecution(); }
RE2::RE2(const std::string &) { RefusePatternExecution(); }
RE2::RE2(const StringPiece &) { RefusePatternExecution(); }
RE2::RE2(const StringPiece &, const Options &) { RefusePatternExecution(); }
RE2::~RE2() {}
RE2::Options::Options(CannedOptions) : Options() { RefusePatternExecution(); }
int RE2::Options::ParseFlags() const { RefusePatternExecution(); }
int RE2::ProgramSize() const { RefusePatternExecution(); }
int RE2::ReverseProgramSize() const { RefusePatternExecution(); }
int RE2::ProgramFanout(std::vector<int> *) const { RefusePatternExecution(); }
int RE2::ReverseProgramFanout(std::vector<int> *) const { RefusePatternExecution(); }
bool RE2::FullMatchN(const StringPiece &, const RE2 &, const Arg *const [], int) { RefusePatternExecution(); }
bool RE2::PartialMatchN(const StringPiece &, const RE2 &, const Arg *const [], int) { RefusePatternExecution(); }
bool RE2::ConsumeN(StringPiece *, const RE2 &, const Arg *const [], int) { RefusePatternExecution(); }
bool RE2::FindAndConsumeN(StringPiece *, const RE2 &, const Arg *const [], int) { RefusePatternExecution(); }
bool RE2::Replace(std::string *, const RE2 &, const StringPiece &) { RefusePatternExecution(); }
int RE2::GlobalReplace(std::string *, const RE2 &, const StringPiece &) { RefusePatternExecution(); }
bool RE2::Extract(const StringPiece &, const RE2 &, const StringPiece &, std::string *) { RefusePatternExecution(); }
std::string RE2::QuoteMeta(const StringPiece &) { RefusePatternExecution(); }
bool RE2::PossibleMatchRange(std::string *, std::string *, int) const { RefusePatternExecution(); }
const std::map<std::string,int> &RE2::NamedCapturingGroups() const { RefusePatternExecution(); }
const std::map<int,std::string> &RE2::CapturingGroupNames() const { RefusePatternExecution(); }
bool RE2::Match(const StringPiece &, size_t, size_t, Anchor, StringPiece *, int) const { RefusePatternExecution(); }
bool RE2::CheckRewriteString(const StringPiece &, std::string *) const { RefusePatternExecution(); }
int RE2::MaxSubmatch(const StringPiece &) { RefusePatternExecution(); }
bool RE2::Rewrite(std::string *, const StringPiece &, const StringPiece *, int) const { RefusePatternExecution(); }
void RE2::FUZZING_ONLY_set_maximum_global_replace_count(int) { RefusePatternExecution(); }
namespace re2_internal {
template <typename T> bool Parse(const char *, size_t, T *) { RefusePatternExecution(); }
template <typename T> bool Parse(const char *, size_t, T *, int) { RefusePatternExecution(); }
}
Regex::Regex(const std::string &, RegexOptions) { RefusePatternExecution(); }
bool RegexSearch(const std::string &, Match &, const Regex &) { RefusePatternExecution(); }
bool RegexMatch(const std::string &, Match &, const Regex &) { RefusePatternExecution(); }
bool RegexMatch(const char *, const char *, Match &, const Regex &) { RefusePatternExecution(); }
bool RegexMatch(const std::string &, const Regex &) { RefusePatternExecution(); }
duckdb::vector<Match> RegexFindAll(const std::string &, const Regex &) { RefusePatternExecution(); }
duckdb::vector<Match> RegexFindAll(const char *, size_t, const RE2 &) { RefusePatternExecution(); }
StringPiece::size_type StringPiece::copy(char *buffer, size_type count, size_type position) const {
 if (position > size_) throw std::out_of_range("byte slice copy position");
 count=std::min(count,size_-position);
 if (count) memcpy(buffer,data_+position,count);
 return count;
}
StringPiece StringPiece::substr(size_type position, size_type count) const {
 if (position > size_) throw std::out_of_range("byte slice substring position");
 return StringPiece(data_ ? data_+position : nullptr,std::min(count,size_-position));
}
StringPiece::size_type StringPiece::find(const StringPiece &value,size_type position) const {
 if (position>size_ || value.size()>size_-position) return npos;
 if (value.empty()) return position;
 for (size_type index=position;index<=size_-value.size();index++)
  if (memcmp(data_+index,value.data(),value.size())==0) return index;
 return npos;
}
StringPiece::size_type StringPiece::find(char value,size_type position) const {
 for (size_type index=position;index<size_;index++) if (data_[index]==value) return index;
 return npos;
}
StringPiece::size_type StringPiece::rfind(const StringPiece &value,size_type position) const {
 if (value.size()>size_) return npos;
 size_type index=std::min(position,size_-value.size());
 if (value.empty()) return index;
 for (;;) { if (memcmp(data_+index,value.data(),value.size())==0) return index; if (!index) return npos; index--; }
}
StringPiece::size_type StringPiece::rfind(char value,size_type position) const {
 if (!size_) return npos;
 size_type index=std::min(position,size_-1);
 for (;;) { if (data_[index]==value) return index; if (!index) return npos; index--; }
}
std::ostream &operator<<(std::ostream &output,const StringPiece &value) { return output.write(value.data(),value.size()); }
}
