import argparse
import os
from collections import defaultdict
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm

def extrair_titulo_e_categoria(pdf_path, base_dir):
    rel_path = os.path.relpath(pdf_path, base_dir)
    parts = rel_path.split(os.sep)
    if len(parts) == 1:
        categoria = "Outros"
        titulo = os.path.splitext(parts[0])[0]
    else:
        categoria = parts[-2].capitalize()
        titulo = os.path.splitext(parts[-1])[0]
    return categoria, titulo

def gerar_indice(categorias_dict, paginas_dict, pasta_raiz, output_pdf="indice_temp.pdf"):
    largura, altura = A4
    c = canvas.Canvas(output_pdf, pagesize=A4)

    # Título principal (nome da pasta raiz)
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(largura / 2, altura - 40 * mm, pasta_raiz.upper())
    y = altura - 60 * mm

    c.setFont("Helvetica-Bold", 14)
    margem_esquerda = 30 * mm
    margem_direita = largura - 30 * mm
    linha_altura = 14

    for categoria, titulos in categorias_dict.items():
        c.drawString(margem_esquerda, y, categoria.upper())
        y -= linha_altura
        c.setFont("Helvetica", 12)
        for titulo in titulos:
            pagina_str = str(paginas_dict[titulo])
            text_width = c.stringWidth(titulo, "Helvetica", 12)
            num_width = c.stringWidth(pagina_str, "Helvetica", 12)
            total_width = margem_direita - margem_esquerda
            pontos_disponiveis = int((total_width - text_width - num_width) / c.stringWidth(".", "Helvetica", 12))
            pontos = "." * pontos_disponiveis

            c.drawString(margem_esquerda, y, f"{titulo} {pontos} {pagina_str}")
            y -= linha_altura
        y -= linha_altura  # espaço extra entre categorias
        c.setFont("Helvetica-Bold", 14)

    c.showPage()
    c.save()

def juntar_pdfs_com_indice(pdfs, output_pdf, capa_pdf=None):
    writer = PdfWriter()
    pagina_atual = 0
    base_dir = os.path.commonpath(pdfs)
    pasta_raiz = os.path.basename(os.path.abspath(base_dir))

    if capa_pdf:
        reader = PdfReader(capa_pdf)
        for page in reader.pages:
            writer.add_page(page)
        pagina_atual += len(reader.pages)

    categorias_dict = defaultdict(list)
    paginas_dict = {}
    pdf_infos = []

    for pdf in pdfs:
        categoria, titulo = extrair_titulo_e_categoria(pdf, base_dir)
        reader = PdfReader(pdf)
        count = len(reader.pages)

        categorias_dict[categoria].append(titulo)
        paginas_dict[titulo] = pagina_atual + 1  # contando com capa e índice
        pdf_infos.append((reader, categoria, titulo))

        pagina_atual += count

    gerar_indice(categorias_dict, paginas_dict, pasta_raiz)

    indice_reader = PdfReader("indice_temp.pdf")
    for page in indice_reader.pages:
        writer.add_page(page)

    # Adiciona PDFs com bookmarks hierárquicos
    categoria_parents = {}
    for reader, categoria, titulo in pdf_infos:
        if categoria not in categoria_parents:
            categoria_parents[categoria] = writer.add_outline_item(categoria, len(writer.pages))
        parent = categoria_parents[categoria]
        bookmark = writer.add_outline_item(titulo, len(writer.pages), parent=parent)
        for page in reader.pages:
            writer.add_page(page)

    with open(output_pdf, "wb") as f:
        writer.write(f)

    os.remove("indice_temp.pdf")
    print(f"✅ PDF final gerado: {output_pdf}")

def main():
    parser = argparse.ArgumentParser(description="Junta PDFs com capa, índice hierárquico e marcadores.")
    parser.add_argument("pdfs", nargs="+", help="Arquivos PDF a juntar (com caminhos organizados em pastas)")
    parser.add_argument("-o", "--output", required=True, help="Nome do PDF de saída")
    parser.add_argument("--cover", help="PDF opcional para usar como capa")
    args = parser.parse_args()

    juntar_pdfs_com_indice(args.pdfs, args.output, args.cover)

if __name__ == "__main__":
    main()
