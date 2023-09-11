MTUOCServer_port=""
MTUOCServer_MTengine=""
startMTEngineV=False
startMTEngineCommand=""
MTUOCServer_type=""
MTEngineIP=""
MTEnginePort=""
verbosity_level=0
log_file=""
sortidalog=""
min_len_factor=0.5
min_chars_segment=1
tag_restoration=False


segment_input=False
SRXfile=None
SRXlang=None
rules=None

sllang=""
tllang=""
tokenize_SL=False
tokenize_TL=False
tokenizerSL=None
tokenizerTL=None
tokenizerSLType=""
tokenizerTLType=""

tcmodel=""
truecase=""
truecaser=None
checkistranslatable=False

MTUOCServer_URLs=False
MTUOCServer_EMAILs=False

code_URLs="@URL@"
code_EMAILs="@EMAIL@"

pre_replace_NUMs=False
code_NUMs="@NUM@"
pre_split_NUMs=False

#sentencepiece
sentencepiece=""
spmodelSL=""
spmodelTL=""
sp_splitter=""

#BPE
BPE=""
bpecodes=""
bpe_joiner=""
bpeobject=None


leading_spaces=0
trailing_spaces=0

MTUOCServer_NUMs=False
MTUOCServer_splitNUMs=False

escape_html_input=False
unescape_html_input=True

change_input_files=None
change_output_files=None
change_translation_files=None
changes_input=[]
changes_output=[]
changes_translation=[]


tagrestorer=None

bos_annotate=False
bos_symbol="<s>"
#None or <s> (or other)
eos_annotate=False
eos_symbol="</s>"

spSL=None
spTL=None

translation_selection_strategy="First"

Google_sllang=""
Google_tllang=""
Google_glossary=""
Google_project_id=""
Google_location=""
Google_jsonfile=""
client=None
parent=None

DeepL_API_key=""
DeepL_sl_lang=""
DeepL_tl_lang=""
DeepL_formality=""
DeepL_split_sentences=""
DeepL_glossary=""
DeepLtranslator=None

Lucy_url=""
Lucy_TRANSLATION_DIRECTION=""
Lucy_MARK_UNKNOWNS=""
Lucy_MARK_ALTERNATIVES=""
Lucy_MARK_COMPOUNDS=""
Lucy_CHARSET=""

MTUOCServer_ONMT_url_root=None

proxyMoses=None
