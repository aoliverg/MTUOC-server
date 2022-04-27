#    MTUOC_simalign
#    Copyright (C) 2022  Antoni Oliver
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

from simalign import SentenceAligner
import codecs
import importlib
import importlib.util


    
class MTUOC_simalign:
    '''Class for automatic terminology extraction and terminology management.'''
    def __init__(self,model="bert",token_type="word",matching_method="m",device="cpu",sltokenizer=None,tltokenizer=None):
        self.aligner= SentenceAligner(model="bert", token_type="bpe", matching_methods=matching_method, device=device)
        if sltokenizer==None:
            self.tokenizerSL=None
        else:
            if not sltokenizer.endswith(".py"): sltokenizer=sltokenizer+".py"
            spec = importlib.util.spec_from_file_location('', sltokenizer)
            tokenizerSLmod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(tokenizerSLmod)
            self.tokenizerSL=tokenizerSLmod.Tokenizer()
        if tltokenizer==None:
            self.tokenizerTL=None
        else:
            if not tltokenizer.endswith(".py"): tltokenizer=tltokenizer+".py"
            spec = importlib.util.spec_from_file_location('', tltokenizer)
            tokenizerTLmod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(tokenizerTLmod)
            self.tokenizerTL=tokenizerTLmod.Tokenizer()
            
        if not matching_method in ["m","a","i"]:
            self.matching_method="a"
        else:
            self.matching_method=matching_method
        
    def convert(self,alignment):
        converted=[]
        for tupla in alignment:
            ali=str(tupla[0])+"-"+str(tupla[1])
            converted.append(ali)
        converted=" ".join(converted)
        return converted
    
    def align_segments(self,segmentL1,segmentL2):
        tokens1=segmentL1.split()
        tokens2=segmentL2.split()
        alignments = self.aligner.get_word_aligns(tokens1, tokens2)
        if self.matching_method=="m":
            alignment=self.convert(alignments["mwmf"])
        elif self.matching_method=="a":
            alignment=self.convert(alignments["inter"])
        elif self.matching_method=="i":
            alignment=self.convert(alignments["itermax"])
        else:
            alignment=self.convert(alignments["mwmf"])
        print("^^^^",segmentL1)
        print("^^^^",segmentL2)
        print("^^^^",alignment)
        return(alignment)
    
    def align_tabbed_file(self,tabbedfile, fileOUT):
        entrada=codecs.open(tabbedfile,"r",encoding="utf-8")
        sortida=codecs.open(fileOUT,"w",encoding="utf-8")
        for linia in entrada:
            linia=linia.rstrip()
            camps=linia.split("\t")
            linia1=camps[0]
            linia2=camps[1]
            if self.tokenizerSL==None:
                tokens1=linia1
            else:
                tokens1=self.tokenizerSL.tokenize(linia1)
            if self.tokenizerTL==None:
                tokens2=linia2
            else:
                tokens2=self.tokenizerTL.tokenize(linia2)    
            alignment=self.align_segments(tokens1,tokens2)
            sortida.write(alignment+"\n")
        sortida.close()
        
    def align_files(self, fileL1, fileL2, fileOUT):
        entrada1=codecs.open(fileL1,"r",encoding="utf-8")
        entrada2=codecs.open(fileL2,"r",encoding="utf-8")
        sortida=codecs.open(fileOUT,"w",encoding="utf-8")
        while 1:
            linia1=entrada1.readline()
            if not linia1:
                break
            linia1=linia1.rstrip()
            linia2=entrada2.readline().rstrip()
            if self.tokenizerSL==None:
                tokens1=linia1
            else:
                tokens1=self.tokenizerSL.tokenize(linia1)
            if self.tokenizerTL==None:
                tokens2=linia2
            else:
                tokens2=self.tokenizerTL.tokenize(linia2)    
            alignment=self.align_segments(tokens1,tokens2)
            sortida.write(alignment+"\n")
        sortida.close()




