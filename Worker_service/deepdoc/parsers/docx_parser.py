from docling.datamodel.base_models import InputFormat

from deepdoc.parsers.docling_parser import DoclingParser


class DocxParser(DoclingParser):
    name = "docx"
    input_format = InputFormat.DOCX
