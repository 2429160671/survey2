

import xlwt


book = xlwt.Workbook()
table = book.add_sheet("sheet1")

table.write(0, 0, "哈哈")
book.save("测试.xls")
