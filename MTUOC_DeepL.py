import config
from MTUOC_misc import printLOG

###DeepL imports
import deepl

def DeepL_translate(segment):
    if config.DeepL_glossary==None:
        cadena="Translating without glossary from "+config.DeepL_sl_lang+" to "+config.DeepL_tl_lang
        printLOG(3,cadena)
        cadena="Source segment: "+segment
        printLOG(3,cadena)
        try:
            translation = config.DeepLtranslator.translate_text(segment, source_lang=config.DeepL_sl_lang, target_lang=config.DeepL_tl_lang,formality=config.DeepL_formality,split_sentences=config.DeepL_split_sentences)
        except:
            printLOG(1,"ERROR DeepL:",sys.exc_info())
        cadena="Translation:    "+translation.text
        printLOG(3,cadena)
    else:
        cadena="Translating with glossary "+config.DeepL_glossary_name,DeepL_glossary+" from "+config.DeepL_sl_lang+" to "+config.DeepL_tl_lang
        printLOG(3,cadena)
        cadena="Source segment: "+segment
        printLOG(3,cadena)
        try:
            translation = config.DeepLtranslator.translate_text(segment, source_lang=config.DeepL_sl_lang, target_lang=config.DeepL_tl_lang, glossary=config.DeepL_glossary, formality=config.DeepL_formality, split_sentences=config.DeepL_split_sentences)
        except:
            printLOG(1,"ERROR DeepL:",sys.exc_info())
        cadena="Translation:    "+translation.text
        printLOG(3,cadena)

    return(translation.text)

