namespace duckdb_libpgquery {
// Explicit byte states replace the existing generated SQL scanner.
struct OwnedSQLLexer {
 core_yy_extra_type *extra;
 size_t cursor;
 size_t held_at;
 char held;
 bool has_held;
 int location;
};
[[noreturn]] static void OwnedSQLFailure(const char *message) {
 ereport(ERROR,(errcode(PG_ERRCODE_SYNTAX_ERROR),errmsg("%s",message)));
 throw std::runtime_error(message);
}
static bool OwnedSQLSpace(unsigned char c) {
 return c==' '||c=='\t'||c=='\n'||c=='\r'||c=='\f'||c=='\v';
}
static bool OwnedSQLDigit(unsigned char c) {return c>='0'&&c<='9';}
static bool OwnedSQLStart(unsigned char c) {
 return c=='_'||c>=128||(c>='a'&&c<='z')||(c>='A'&&c<='Z');
}
static bool OwnedSQLContinue(unsigned char c) {return OwnedSQLStart(c)||OwnedSQLDigit(c)||c=='$';}
static int OwnedSQLHex(unsigned char c) {
 if(c>='0'&&c<='9')return c-'0';
 if(c>='a'&&c<='f')return c-'a'+10;
 if(c>='A'&&c<='F')return c-'A'+10;
 return -1;
}
static void OwnedSQLUTF8(const char *data,size_t length) {
 for(size_t at=0;at<length;){
  unsigned char c=data[at++];
  if(c<128){if(!c)OwnedSQLFailure("zero byte in SQL source");continue;}
  unsigned count=0;uint32_t value=0,minimum=0;
  if(c>=0xc2&&c<=0xdf){count=1;value=c&31;minimum=0x80;}
  else if(c>=0xe0&&c<=0xef){count=2;value=c&15;minimum=0x800;}
  else if(c>=0xf0&&c<=0xf4){count=3;value=c&7;minimum=0x10000;}
  else OwnedSQLFailure("invalid UTF-8 in SQL source");
  if(count>length-at)OwnedSQLFailure("unfinished UTF-8 in SQL source");
  for(unsigned n=0;n<count;n++) {c=data[at++];if(c<0x80||c>0xbf)OwnedSQLFailure("invalid UTF-8 continuation in SQL source");value=(value<<6)|(c&63);}
  if(value<minimum||value>0x10ffff||(value>=0xd800&&value<=0xdfff))OwnedSQLFailure("invalid UTF-8 scalar in SQL source");
 }
}
static char *OwnedSQLCopy(const std::string &text) {
 if(text.find('\0')!=std::string::npos)OwnedSQLFailure("zero byte in SQL literal");
 char *result=static_cast<char *>(palloc(text.size()+1));
 memcpy(result,text.data(),text.size());result[text.size()]=0;return result;
}
static size_t OwnedSQLTrivia(const char *data,size_t size,size_t at,bool &newline,bool block_comments=true) {
 while(at<size){
  if(OwnedSQLSpace(data[at])){newline=newline||data[at]=='\n'||data[at]=='\r';at++;continue;}
  if(at+1<size&&data[at]=='-'&&data[at+1]=='-'){
   at+=2;while(at<size&&data[at]!='\n'&&data[at]!='\r')at++;continue;
  }
  if(block_comments&&at+1<size&&data[at]=='/'&&data[at+1]=='*'){
   at+=2;size_t depth=1;
   while(depth&&at<size){
    if(at+1<size&&data[at]=='/'&&data[at+1]=='*'){depth++;at+=2;}
    else if(at+1<size&&data[at]=='*'&&data[at+1]=='/'){depth--;at+=2;}
    else {newline=newline||data[at]=='\n'||data[at]=='\r';at++;}
   }
   if(depth)OwnedSQLFailure("unterminated SQL block comment");continue;
  }
  break;
 }
 return at;
}
static std::string OwnedSQLQuoted(const char *data,size_t size,size_t &at,char quote,bool escapes,bool continuation) {
 std::string out;at++;
 for(;;){
  if(at>=size)OwnedSQLFailure("unterminated SQL quoted value");
  char c=data[at++];
  if(c==quote){
   if(at<size&&data[at]==quote){out.push_back(quote);at++;continue;}
   if(continuation){bool newline=false;size_t next=OwnedSQLTrivia(data,size,at,newline,false);if(newline&&next<size&&data[next]==quote){at=next+1;continue;}}
   break;
  }
  if(c!='\\'||!escapes){out.push_back(c);continue;}
  if(at>=size)OwnedSQLFailure("unfinished escape in SQL literal");
  c=data[at++];
  switch(c){
   case 'b':out.push_back('\b');break;case 'f':out.push_back('\f');break;case 'n':out.push_back('\n');break;
   case 'r':out.push_back('\r');break;case 't':out.push_back('\t');break;
   case 'u':case 'U':OwnedSQLFailure("Unicode escape conversion is unsupported by this reference driver");
   case 'x':{
    unsigned value=0,count=0;
    while(count<2&&at<size&&OwnedSQLHex(data[at])>=0){value=(value<<4)|unsigned(OwnedSQLHex(data[at++]));count++;}
    if(!count)out.push_back('x');else {if(!value)OwnedSQLFailure("zero byte in SQL literal");out.push_back(char(value));}break;
   }
   default:
    if(c>='0'&&c<='7'){
     unsigned value=c-'0',count=1;
     while(count<3&&at<size&&data[at]>='0'&&data[at]<='7'){value=(value<<3)|unsigned(data[at++]-'0');count++;}
     if(!(value&255))OwnedSQLFailure("zero byte in SQL literal");out.push_back(char(value&255));
    }else out.push_back(c);
  }
 }
 OwnedSQLUTF8(out.data(),out.size());return out;
}
static bool OwnedSQLWord(const char *data,size_t size,size_t at,const char *word) {
 size_t index=0;
 for(;word[index];index++){
  if(at+index>=size)return false;unsigned char c=data[at+index];if(c>='A'&&c<='Z')c+=32;if(c!=word[index])return false;
 }
 return at+index==size||!OwnedSQLContinue(data[at+index]);
}
static std::string OwnedSQLUnicodeQuoted(const char *data,size_t size,size_t &at,char quote) {
 std::string raw=OwnedSQLQuoted(data,size,at,quote,false,quote=='\'');char escape='\\';
 bool newline=false;size_t next=OwnedSQLTrivia(data,size,at,newline);
 if(OwnedSQLWord(data,size,next,"uescape")){
  next+=7;next=OwnedSQLTrivia(data,size,next,newline);
  if(next+2>=size||data[next]!='\''||data[next+2]!='\'')OwnedSQLFailure("invalid SQL Unicode escape declaration");
  escape=data[next+1];if(OwnedSQLHex(escape)>=0||escape=='+'||escape=='\''||escape=='"'||OwnedSQLSpace(escape)||static_cast<unsigned char>(escape)>=128)OwnedSQLFailure("invalid SQL Unicode escape character");
  at=next+3;
 }
 std::string out;
 for(size_t index=0;index<raw.size();){
  char c=raw[index++];if(c!=escape){out.push_back(c);continue;}
  if(index<raw.size()&&raw[index]==escape){out.push_back(escape);index++;continue;}
  OwnedSQLFailure("Unicode escape conversion is unsupported by this reference driver");
 }
 OwnedSQLUTF8(out.data(),out.size());return out;
}
core_yyscan_t scanner_init(const char *text,core_yy_extra_type *extra,const PGScanKeyword *keywords,int count) {
 size_t size=strlen(text);if(size>static_cast<size_t>(2147483647-2))OwnedSQLFailure("SQL source exceeds parser byte bound");
 OwnedSQLUTF8(text,size);
 auto state=static_cast<OwnedSQLLexer *>(palloc(sizeof(OwnedSQLLexer)));memset(state,0,sizeof(*state));state->extra=extra;
 extra->scanbuf=static_cast<char *>(palloc(size+2));memcpy(extra->scanbuf,text,size);extra->scanbuf[size]=extra->scanbuf[size+1]=0;
 extra->scanbuflen=size;extra->keywords=keywords;extra->num_keywords=count;
 extra->backslash_quote=2;extra->escape_string_warning=true;extra->standard_conforming_strings=true;
 extra->literalbuf=nullptr;extra->literallen=extra->literalalloc=0;
 return state;
}
void scanner_finish(core_yyscan_t scanner) {
 auto state=static_cast<OwnedSQLLexer *>(scanner);pfree(state->extra->scanbuf);state->extra->scanbuf=nullptr;pfree(state);
}
int scanner_errposition(int location,core_yyscan_t scanner) {
 if(location<0)return 0;
 auto state=static_cast<OwnedSQLLexer *>(scanner);
 return errposition(pg_mbstrlen_with_len(state->extra->scanbuf,location)+1);
}
void scanner_yyerror(const char *message,core_yyscan_t scanner) {
 auto state=static_cast<OwnedSQLLexer *>(scanner);
 ereport(ERROR,(errcode(PG_ERRCODE_SYNTAX_ERROR),errmsg("%s",message),scanner_errposition(state->location,scanner)));
}
int core_yylex(core_YYSTYPE *value,int *location,core_yyscan_t scanner) {
 auto state=static_cast<OwnedSQLLexer *>(scanner);auto extra=state->extra;char *data=extra->scanbuf;size_t size=extra->scanbuflen;
 if(state->has_held){data[state->held_at]=state->held;state->has_held=false;}
 bool newline=false;size_t at=OwnedSQLTrivia(data,size,state->cursor,newline),start=at;
 *location=state->location=static_cast<int>(at);
 auto finish=[&](int token){state->cursor=at;state->held_at=at;state->held=data[at];state->has_held=true;data[at]=0;return token;};
 if(at==size)return finish(0);
 unsigned char c=data[at];
 if(c=='"'){std::string text=OwnedSQLQuoted(data,size,at,'"',false,false);if(text.empty())OwnedSQLFailure("zero length SQL identifier");value->str=OwnedSQLCopy(text);return finish(IDENT);}
 if((c=='U'||c=='u')&&at+2<size&&data[at+1]=='&'&&(data[at+2]=='\''||data[at+2]=='"')){
  at+=2;char quote=data[at];std::string text=OwnedSQLUnicodeQuoted(data,size,at,quote);
  if(quote=='"'&&text.empty())OwnedSQLFailure("zero length SQL identifier");value->str=OwnedSQLCopy(text);return finish(quote=='"'?IDENT:SCONST);
 }
 if((c=='N'||c=='n')&&at+1<size&&data[at+1]=='\''){
  auto keyword=ScanKeywordLookup("nchar",extra->keywords,extra->num_keywords);
  if(!keyword)OwnedSQLFailure("national string keyword is absent");
  at++;value->keyword=keyword->name;return finish(keyword->value);
 }
 if(c=='\''||((c=='E'||c=='e'||c=='B'||c=='b'||c=='X'||c=='x')&&at+1<size&&data[at+1]=='\'')){
  bool prefix=c!='\'';bool escapes=prefix&&(c=='E'||c=='e');bool bits=prefix&&(c=='B'||c=='b');bool hex=prefix&&(c=='X'||c=='x');
  if(prefix)at++;std::string text=OwnedSQLQuoted(data,size,at,'\'',escapes||!extra->standard_conforming_strings,true);
  if(bits)text.insert(text.begin(),'b');if(hex)text.insert(text.begin(),'x');value->str=OwnedSQLCopy(text);return finish(bits?BCONST:hex?XCONST:SCONST);
 }
 if(c=='$'){
  size_t delimiter_end=at+1;
  if(delimiter_end<size&&OwnedSQLStart(data[delimiter_end])){
   delimiter_end++;while(delimiter_end<size&&(OwnedSQLStart(data[delimiter_end])||OwnedSQLDigit(data[delimiter_end])))delimiter_end++;
  }
  if(delimiter_end<size&&data[delimiter_end]=='$'){
   std::string delimiter(data+at,delimiter_end-at+1);size_t body=delimiter_end+1,end=body;
   for(;end<size;end++)if(data[end]=='$'&&delimiter.size()<=size-end&&memcmp(data+end,delimiter.data(),delimiter.size())==0)break;
   if(end==size)OwnedSQLFailure("unterminated SQL dollar quoted string");value->str=OwnedSQLCopy(std::string(data+body,end-body));at=end+delimiter.size();return finish(SCONST);
  }
 }
 if((c=='$'||c=='?')&&at+1<size&&OwnedSQLDigit(data[at+1])){
  at++;uint64_t number=0;
  while(at<size){if(OwnedSQLDigit(data[at])){number=number*10+unsigned(data[at++]-'0');if(number>2147483647)OwnedSQLFailure("SQL parameter number exceeds parser bound");}
   else if(data[at]=='_'&&at+1<size&&OwnedSQLDigit(data[at+1]))at++;else break;}
  value->ival=static_cast<int>(number);return finish(PARAM);
 }
 if(OwnedSQLStart(c)){
  at++;while(at<size&&OwnedSQLContinue(data[at]))at++;
  std::string text(data+start,at-start);auto keyword=ScanKeywordLookup(text.c_str(),extra->keywords,extra->num_keywords);
  if(keyword){value->keyword=keyword->name;return finish(keyword->value);}
  value->str=downcase_truncate_identifier(text.c_str(),static_cast<int>(text.size()),true);return finish(IDENT);
 }
 if(OwnedSQLDigit(c)||(c=='.'&&at+1<size&&OwnedSQLDigit(data[at+1]))){
  bool floating=false;
  auto digits=[&](){while(at<size){if(OwnedSQLDigit(data[at]))at++;else if(data[at]=='_'&&at+1<size&&OwnedSQLDigit(data[at+1]))at++;else break;}};
  digits();if(at<size&&data[at]=='.'&&!(at+1<size&&data[at+1]=='.')){floating=true;at++;digits();}
  if(at<size&&(data[at]=='e'||data[at]=='E')){size_t exponent=at+1;if(exponent<size&&(data[exponent]=='+'||data[exponent]=='-'))exponent++;if(exponent<size&&OwnedSQLDigit(data[exponent])){floating=true;at=exponent;digits();}}
  std::string text(data+start,at-start);
  if(floating){value->str=OwnedSQLCopy(text);return finish(FCONST);}
  uint64_t number=0;bool large=false;std::string normalized;
  for(char digit:text){if(digit=='_')continue;normalized.push_back(digit);if(!large){number=number*10+unsigned(digit-'0');large=number>2147483647;}}
  if(large){value->str=OwnedSQLCopy(normalized);return finish(FCONST);}value->ival=static_cast<int>(number);return finish(ICONST);
 }
 struct Pair {const char *text;int token;};
 const Pair punctuation[]={{"::",TYPECAST},{"..",DOT_DOT},{":=",COLON_EQUALS}};
 for(auto &pair:punctuation){size_t length=strlen(pair.text);if(length<=size-at&&memcmp(data+at,pair.text,length)==0){at+=length;return finish(pair.token);}}
 if(c==':'){at++;return finish(SINGLE_COLON);}
 const char *operators="~!@^&|`+-*/%<>=";
 if(strchr(operators,c)){
  size_t raw_end=at+1;while(raw_end<size&&strchr(operators,data[raw_end]))raw_end++;
  const Pair special[]={{"->>",DOUBLE_ARROW},{"->",SINGLE_ARROW},{"**",POWER_OF},{"//",INTEGER_DIVISION},{"=>",EQUALS_GREATER},{"<=",LESS_EQUALS},{">=",GREATER_EQUALS},{"<>",NOT_EQUALS},{"!=",NOT_EQUALS}};
  for(auto &pair:special){size_t length=strlen(pair.text);if(length==raw_end-at&&memcmp(data+at,pair.text,length)==0){at=raw_end;return finish(pair.token);}}
  at=start+1;
  while(at<raw_end){if(at+1<size&&((data[at]=='/'&&data[at+1]=='*')||(data[at]=='-'&&data[at+1]=='-')))break;at++;}
  while(at-start>1&&(data[at-1]=='+'||data[at-1]=='-')){bool non_sql=false;for(size_t n=start;n+1<at;n++)if(strchr("~!@^&|`%",data[n]))non_sql=true;if(non_sql)break;at--;}
  size_t length=at-start;if(length>=64)OwnedSQLFailure("SQL operator exceeds parser byte bound");
  if(length==1&&strchr(",()[].;:+-*/%^<>=?",c))return finish(c);
  if(length==2){
   const Pair comparisons[]={{"=>",EQUALS_GREATER},{"<=",LESS_EQUALS},{">=",GREATER_EQUALS},{"<>",NOT_EQUALS},{"!=",NOT_EQUALS}};
   for(auto &pair:comparisons)if(memcmp(data+start,pair.text,2)==0)return finish(pair.token);
  }
  value->str=OwnedSQLCopy(std::string(data+start,length));return finish(Op);
 }
 at++;return finish(c);
}
}
