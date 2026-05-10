from docling.datamodel.base_models import InputFormat

from deepdoc.parsers.docling_parser import DoclingParser


class ExcelParser(DoclingParser):
    name = "xlsx"
    input_format = InputFormat.XLSX
