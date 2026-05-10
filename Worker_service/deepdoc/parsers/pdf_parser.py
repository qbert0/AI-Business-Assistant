from docling.datamodel.base_models import InputFormat

from deepdoc.parsers.docling_parser import DoclingParser


class PdfParser(DoclingParser):
    name = "pdf"
    input_format = InputFormat.PDF
