
import win32com.client
import os

TVM_PATH = r"C:\Users\z0034gl\Documents\python_projects\apollo\TVM Calculator - AutoImport.xlsm"
FILE_NAME = "TVM Calculator - AutoImport.xlsm"


def write_to_tvm(df, timestamp, threshold):

    try:
        excel = win32com.client.GetActiveObject("Excel.Application")
    except:
        excel = win32com.client.Dispatch("Excel.Application")
        excel.Visible = True

    wb = None

    for book in excel.Workbooks:
        if book.Name == FILE_NAME:
            wb = book
            print("📂 Using already open workbook")
            break

    if wb is None:
        print("📂 Opening workbook fresh")
        wb = excel.Workbooks.Open(os.path.abspath(TVM_PATH))

    ws = wb.Sheets("Apollo Dock Status")

    # ✅ Clear table
    ws.Range("A2:N1000").ClearContents()

    data = df.values.tolist()
    rows = len(data)
    cols = len(data[0])

    ws.Range(ws.Cells(2, 1), ws.Cells(2 + rows - 1, cols)).Value = data

    # ✅ WRITE TIMESTAMP
    if timestamp:
        ws.Range("AB1").Value = timestamp
    
    # ✅ Update threshold
    ws.Range("Z1").Value = threshold

    if not wb.ReadOnly:
        wb.Save()
    else:
        print("⚡ Workbook already open — no save needed")

    print("✅ Excel updated")
