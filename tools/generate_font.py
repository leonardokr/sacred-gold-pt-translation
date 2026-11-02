"""
Sacred Gold Carolingia Font Accented Glyph Generator.
Reconstructs missing accented glyphs in CAROLING.TTF TrueType tables.
"""

import os
import io
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import Glyph, GlyphCoordinates
from fontTools.ttLib.tables.ttProgram import Program
from PIL import Image, ImageFont, ImageDraw

def generate_accented_carolingia(src_ttf_path, output_ttf_path, preview_png_path=None):
    """
    Builds accented Portuguese characters into the Carolingia font and generates an optional preview image.
    """
    font = TTFont(src_ttf_path)
    glyf = font['glyf']
    hmtx = font['hmtx']
    
    def extract_contour_data(glyph_name, contour_indices):
        """
        Extracts specific contour coordinates, end points, and flags from a glyph.
        """
        g = glyf[glyph_name]

        coords, end_pts, flags = g.getCoordinates(glyf)
        all_pts = []
        all_flags = []
        new_end_pts = []
        for c_idx in contour_indices:
            sp = end_pts[c_idx - 1] + 1 if c_idx > 0 else 0
            ep = end_pts[c_idx]
            pts = coords[sp:ep+1]
            flgs = flags[sp:ep+1]
            all_pts.extend(pts)
            all_flags.extend(flgs)
            new_end_pts.append(len(all_pts) - 1)
        return all_pts, new_end_pts, all_flags

    pts_acute_lc, _, flags_acute_lc = extract_contour_data('aacute', [2])
    pts_acute_uc, _, flags_acute_uc = extract_contour_data('Eacute', [1])
    
    pts_grave_lc, _, flags_grave_lc = extract_contour_data('agrave', [2])
    pts_grave_uc, _, flags_grave_uc = extract_contour_data('Agrave', [2])

    pts_tilde_lc, _, flags_tilde_lc = extract_contour_data('ntilde', [1])
    pts_tilde_uc, _, flags_tilde_uc = extract_contour_data('Ntilde', [1])

    pts_circ_lc, _, flags_circ_lc = extract_contour_data('acircumflex', [2])
    pts_circ_uc, _, flags_circ_uc = extract_contour_data('Ecircumflex', [1])

    pts_dier_lc, _, flags_dier_lc = extract_contour_data('adieresis', [2, 3])
    pts_dier_uc, _, flags_dier_uc = extract_contour_data('Adieresis', [2, 3])

    accents = {
        'acute_lc': (pts_acute_lc, flags_acute_lc),
        'acute_uc': (pts_acute_uc, flags_acute_uc),
        'grave_lc': (pts_grave_lc, flags_grave_lc),
        'grave_uc': (pts_grave_uc, flags_grave_uc),
        'tilde_lc': (pts_tilde_lc, flags_tilde_lc),
        'tilde_uc': (pts_tilde_uc, flags_tilde_uc),
        'circ_lc':  (pts_circ_lc, flags_circ_lc),
        'circ_uc':  (pts_circ_uc, flags_circ_uc),
        'dier_lc':  (pts_dier_lc, flags_dier_lc),
        'dier_uc':  (pts_dier_uc, flags_dier_uc),
    }

    def build_glyph(target_name, base_name, accent_key, base_contour_indices=None, y_offset=0, x_offset=0):
        """
        Combines a base glyph with an accent contour to create an accented character.
        """
        g_base = glyf[base_name]

        coords_b, end_pts_b, flags_b = g_base.getCoordinates(glyf)
        
        if base_contour_indices is not None:
            base_pts = []
            base_flags = []
            new_base_ends = []
            for ci in base_contour_indices:
                sp = end_pts_b[ci - 1] + 1 if ci > 0 else 0
                ep = end_pts_b[ci]
                base_pts.extend(coords_b[sp:ep+1])
                base_flags.extend(flags_b[sp:ep+1])
                new_base_ends.append(len(base_pts) - 1)
        else:
            base_pts = list(coords_b)
            base_flags = list(flags_b)
            new_base_ends = list(end_pts_b)

        base_xs = [p[0] for p in base_pts]
        base_ys = [p[1] for p in base_pts]
        base_mid_x = (min(base_xs) + max(base_xs)) / 2
        base_top_y = max(base_ys)

        acc_pts, acc_flags = accents[accent_key]
        acc_xs = [p[0] for p in acc_pts]
        acc_ys = [p[1] for p in acc_pts]
        acc_mid_x = (min(acc_xs) + max(acc_xs)) / 2
        acc_min_y = min(acc_ys)

        dx = round(base_mid_x - acc_mid_x) + x_offset
        
        if 'tilde' in accent_key:
            if 'uc' in accent_key:
                target_min_y = max(598, base_top_y + 14)
            else:
                target_min_y = max(306, base_top_y + 20)
        elif 'uc' in accent_key:
            target_min_y = max(acc_min_y, base_top_y + 16)
        else:
            target_min_y = max(295, base_top_y + 10)
            
        dy = (target_min_y - acc_min_y) + y_offset

        shifted_acc = [(x + dx, y + dy) for x, y in acc_pts]

        combined_pts = base_pts + shifted_acc
        combined_flags = base_flags + acc_flags
        
        if accent_key in ['dier_lc', 'dier_uc']:
            half1_len = 18 if accent_key == 'dier_lc' else 18
            combined_ends = new_base_ends + [len(base_pts) + half1_len - 1, len(combined_pts) - 1]
        else:
            combined_ends = new_base_ends + [len(combined_pts) - 1]

        new_g = Glyph()
        new_g.numberOfContours = len(combined_ends)
        new_g.coordinates = GlyphCoordinates(combined_pts)
        new_g.endPtsOfContours = combined_ends
        new_g.flags = bytearray(combined_flags)
        new_g.program = Program()
        new_g.recalcBounds(glyf)

        glyf[target_name] = new_g
        hmtx[target_name] = (hmtx[base_name][0], new_g.xMin)

    build_glyph('atilde', 'a', 'tilde_lc')
    build_glyph('iacute', 'i', 'acute_lc', base_contour_indices=[0])
    build_glyph('igrave', 'i', 'grave_lc', base_contour_indices=[0])
    build_glyph('icircumflex', 'i', 'circ_lc', base_contour_indices=[0])
    build_glyph('idieresis', 'i', 'dier_lc', base_contour_indices=[0])
    build_glyph('oacute', 'o', 'acute_lc')
    build_glyph('ograve', 'o', 'grave_lc')
    build_glyph('otilde', 'o', 'tilde_lc')
    build_glyph('uacute', 'u', 'acute_lc')
    build_glyph('ugrave', 'u', 'grave_lc')
    build_glyph('ucircumflex', 'u', 'circ_lc')
    build_glyph('egrave', 'e', 'grave_lc')
    build_glyph('yacute', 'y', 'acute_lc')

    build_glyph('Atilde', 'A', 'tilde_uc')
    build_glyph('Iacute', 'I', 'acute_uc')
    build_glyph('Igrave', 'I', 'grave_uc')
    build_glyph('Icircumflex', 'I', 'circ_uc')
    build_glyph('Idieresis', 'I', 'dier_uc')
    build_glyph('Oacute', 'O', 'acute_uc')
    build_glyph('Ograve', 'O', 'grave_uc')
    build_glyph('Otilde', 'O', 'tilde_uc')
    build_glyph('Uacute', 'U', 'acute_uc')
    build_glyph('Ugrave', 'U', 'grave_uc')
    build_glyph('Ucircumflex', 'U', 'circ_uc')
    build_glyph('Yacute', 'Y', 'acute_uc')

    for t_name in ['tilde', 'asciitilde']:
        acc_pts, acc_flags = accents['tilde_lc']
        dx = round(230 - ((min(p[0] for p in acc_pts) + max(p[0] for p in acc_pts))/2))
        dy = -50
        pts = [(x + dx, y + dy) for x, y in acc_pts]
        g = Glyph()
        g.numberOfContours = 1
        g.coordinates = GlyphCoordinates(pts)
        g.endPtsOfContours = [len(pts) - 1]
        g.flags = bytearray(acc_flags)
        g.program = Program()
        g.recalcBounds(glyf)
        glyf[t_name] = g
        hmtx[t_name] = (460, g.xMin)

    os.makedirs(os.path.dirname(os.path.abspath(output_ttf_path)), exist_ok=True)
    font.save(output_ttf_path)
    print(f"Font saved to: {output_ttf_path}")

    if preview_png_path:
        buf = io.BytesIO()
        font.save(buf)
        buf.seek(0)
        
        pil_font_large = ImageFont.truetype(buf, 28)
        buf.seek(0)
        pil_font_medium = ImageFont.truetype(buf, 20)

        img = Image.new('RGB', (650, 420), color=(24, 24, 28))
        draw = ImageDraw.Draw(img)

        lines = [
            ("NOVO JOGO  -  CARREGAR  -  OPÇÕES", pil_font_large, (230, 205, 130)),
            ("INICIAR AVENTURA  -  CRÉDITOS  -  SAÍDA", pil_font_large, (230, 205, 130)),
            ("Missões  -  Poções  -  Música  -  Herói", pil_font_medium, (240, 240, 240)),
            ("Configurações de Áudio e Vídeo", pil_font_medium, (200, 200, 200)),
            ("á à ã â é ê í ó ô õ ú ç", pil_font_medium, (140, 215, 255)),
            ("Á À Ã Â É Ê Í Ó Ô Õ Ú Ç", pil_font_medium, (140, 215, 255)),
        ]

        y = 25
        for text, f, color in lines:
            draw.text((30, y), text, font=f, fill=color)
            y += 62

        os.makedirs(os.path.dirname(os.path.abspath(preview_png_path)), exist_ok=True)
        img.save(preview_png_path)
        print(f"Preview saved to: {preview_png_path}")

if __name__ == "__main__":
    game_font = r"C:\Program Files (x86)\Steam\steamapps\common\Sacred Gold\font\CAROLING.TTF"
    repo_font = os.path.join(os.path.dirname(__file__), "..", "font", "CAROLING.TTF")
    preview = os.path.join(os.path.dirname(__file__), "..", "font", "preview_carolingia.png")
    generate_accented_carolingia(game_font, repo_font, preview)
