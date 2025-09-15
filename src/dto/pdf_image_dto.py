class pdf_image_dto:

    def __init__(self, file_id, page_number):
        self._file_id = file_id
        self._page_number = page_number
        self._analysis_result = None
        self._image_path = None

    def __str__(self):
        return (f"file_id={self.file_id}, "
                f"pdf_image_dto(page_number={self.page_number}, "
                f"analysis_result='{self.analysis_result}', "
                f"image_path='{self.image_path}' "
                )

    @property
    def file_id(self):
        return self._file_id

    @file_id.setter
    def file_id(self, value):
        self._file_id = value

    @property
    def page_number(self):
        return self._page_number

    @page_number.setter
    def page_number(self, value):
        self._page_number = value

    @property
    def analysis_result(self):
        return self._analysis_result

    @analysis_result.setter
    def analysis_result(self, value):
        self._analysis_result = value

    @property
    def image_path(self):
        return self._image_path

    @image_path.setter
    def image_path(self, value):
        self._image_path = value
