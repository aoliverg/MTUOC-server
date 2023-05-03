from MTUOC_misc import printLOG
import config

###GoogleTranslate imports
from google.cloud import translate as translateGoogle
from google.cloud import translate

def Google_translate_text_with_glossary(text):
    
    glossary = config.client.glossary_path(
        config.Google_project_id, config.Google_location, config.Google_glossary 
    )

    glossary_config = translateGoogle.TranslateTextGlossaryConfig(glossary=config.Google_glossary)

    # Supported language codes: https://cloud.google.com/translate/docs/languages
    response = client.translate_text(
        request={
            "contents": [text],
            "target_language_code": config.Google_sllang,
            "source_language_code": config.Google_tllang,
            "parent": config.parent,
            "glossary_config": glossary_config,
        }
    )
    translation=response.glossary_translations[0]
    return(translation.translated_text)

def Google_translate_text(text):
    try:
        """Translating Text. segment,config.Google_sllang,config.Google_tllang"""
        # Detail on supported types can be found here:
        # https://cloud.google.com/translate/docs/supported-formats
        response = config.client.translate_text(
            parent=config.parent,
            contents=[text],
            mime_type="text/plain",  # mime types: text/plain, text/html
            source_language_code=config.Google_sllang,
            target_language_code=config.Google_tllang,
        )
        # Display the translation for each input text provided
        translation=response.translations[0]
        return(translation.translated_text)
    except:
        print("ERROR:",sys.exc_info())

    
def Google_translate(segment):
    segment=segment.rstrip()
    if config.Google_glossary==None:
        cadena="Translating without glossary from "+config.Google_sllang+" to "+config.Google_tllang
        printLOG(3,cadena)
        cadena="Source segment: "+segment
        printLOG(3,cadena)
        translation=Google_translate_text(segment)
        cadena="Translation:    "+translation
        printLOG(3,cadena)
    else:
        cadena="Translating with glossary "+Google_glossary+" from "+config.Google_sllang+" to "+config.Google_tllang
        printLOG(3,cadena)
        cadena="Source segment: "+segment
        printLOG(3,cadena)
        translation=Google_translate_text_with_glossary()
        cadena="Translation:    "+translation
        printLOG(3,cadena)
    return(translation)