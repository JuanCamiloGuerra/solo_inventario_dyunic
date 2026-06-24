Attribute VB_Name = "ExportarInventarioGithub"
Option Explicit

Private Const REPO_PATH As String = "C:\Users\juanc\Documents\excel-hithub"
Private Const DATA_FILE As String = "inventario.csv"

Public Sub github_1()
    Dim wsOrigen As Worksheet
    Dim wsDestino As Worksheet
    Dim rangoTabla As Range
    Dim archivoCsv As String

    Set wsOrigen = ThisWorkbook.Worksheets("TB INVENTARIO")
    Set wsDestino = ThisWorkbook.Worksheets("inventario_github")

    Set rangoTabla = wsOrigen.Range("A4").CurrentRegion

    wsDestino.Cells.ClearContents
    wsDestino.Range("A1").Resize(rangoTabla.Rows.Count, rangoTabla.Columns.Count).Value = rangoTabla.Value

    archivoCsv = REPO_PATH & "\" & DATA_FILE
    ExportarHojaComoCsv wsDestino, archivoCsv

    SubirArchivoAGithub REPO_PATH, DATA_FILE

    wsDestino.Activate
    MsgBox "Inventario exportado y enviado a GitHub.", vbInformation
End Sub

Private Sub ExportarHojaComoCsv(ByVal ws As Worksheet, ByVal rutaArchivo As String)
    Dim stream As Object
    Dim rng As Range
    Dim fila As Long
    Dim columna As Long
    Dim linea As String

    Set rng = ws.UsedRange

    Set stream = CreateObject("ADODB.Stream")
    stream.Type = 2
    stream.Charset = "utf-8"
    stream.Open

    For fila = 1 To rng.Rows.Count
        linea = ""

        For columna = 1 To rng.Columns.Count
            If columna > 1 Then linea = linea & ","
            linea = linea & CsvEscape(rng.Cells(fila, columna).Text)
        Next columna

        stream.WriteText linea & vbCrLf
    Next fila

    stream.SaveToFile rutaArchivo, 2
    stream.Close
End Sub

Private Function CsvEscape(ByVal valor As String) As String
    valor = Replace(valor, """", """""")
    CsvEscape = """" & valor & """"
End Function

Private Sub SubirArchivoAGithub(ByVal repoPath As String, ByVal dataFile As String)
    Dim shell As Object
    Dim comando As String
    Dim resultado As Long

    Set shell = CreateObject("WScript.Shell")

    comando = "cmd /c cd /d " & Quote(repoPath) & _
              " && git pull --rebase --autostash" & _
              " && git add " & Quote(dataFile) & _
              " && (git diff --cached --quiet || git commit -m " & Quote("Actualizar inventario desde Excel") & ")" & _
              " && git push"

    resultado = shell.Run(comando, 1, True)

    If resultado <> 0 Then
        MsgBox "No se pudo subir el inventario a GitHub. Revisa la ventana de Git o tus credenciales.", vbExclamation
    End If
End Sub

Private Function Quote(ByVal texto As String) As String
    Quote = """" & texto & """"
End Function
