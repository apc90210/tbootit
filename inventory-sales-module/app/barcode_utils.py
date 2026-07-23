import io

# Code128 patterns for pure python fallback
CODE128_PATTERNS = [
    "212222", "222122", "222221", "121223", "121322", "131222", "122213", "122312", "132212", "221213",
    "221312", "231212", "112232", "122132", "122231", "113222", "123122", "123221", "223211", "221132",
    "221231", "213212", "223112", "312131", "311222", "321122", "321211", "312212", "322112", "322211",
    "212123", "212321", "232121", "111323", "131123", "131321", "112313", "132113", "132311", "211313",
    "231113", "231311", "112133", "112331", "132131", "113123", "113321", "133121", "313121", "211331",
    "231131", "213113", "213311", "213131", "311123", "311321", "331121", "312113", "312311", "332111",
    "314111", "221411", "431111", "111224", "111422", "121124", "121421", "141122", "141221", "112214",
    "112412", "122114", "122411", "142112", "142211", "241211", "221114", "413111", "241112", "134111",
    "111242", "121142", "121241", "114212", "124112", "124211", "411212", "421112", "421211", "212141",
    "214121", "412121", "111143", "111341", "131141", "114113", "114311", "411113", "411311", "113141",
    "114131", "311141", "411131", "211412", "211214", "211232", "2331112"
]

def generate_code128_svg_fallback(data: str) -> str:
    """Pure python Code128B SVG generator fallback."""
    if not data:
        data = "000000000000"
        
    # Start B = 104
    symbols = [104]
    for char in data:
        code_val = ord(char) - 32
        if 0 <= code_val <= 95:
            symbols.append(code_val)
        else:
            symbols.append(0) # space for unencodable
            
    # Checksum calculation
    checksum = symbols[0]
    for idx, val in enumerate(symbols[1:], start=1):
        checksum += idx * val
    checksum %= 103
    symbols.append(checksum)
    
    # Stop symbol = 106
    symbols.append(106)
    
    # Build pattern bars
    pattern = ""
    for s in symbols:
        pattern += CODE128_PATTERNS[s]
        
    # Render SVG rects
    module_width = 1.8
    height = 40
    x = 10
    svg_bars = []
    
    is_bar = True
    for digit in pattern:
        w = int(digit) * module_width
        if is_bar:
            svg_bars.append(f'<rect x="{x:.1f}" y="0" width="{w:.1f}" height="{height}" fill="#000"/>')
        x += w
        is_bar = not is_bar
        
    total_width = x + 10
    
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {total_width:.1f} {height + 15}" width="100%" height="100%">
    <g>
        {''.join(svg_bars)}
        <text x="{total_width / 2:.1f}" y="{height + 12}" font-family="monospace" font-size="11" font-weight="bold" text-anchor="middle" fill="#000">{data}</text>
    </g>
</svg>'''
    return svg

def render_barcode_svg(code_str: str) -> str:
    """Renders Code128 SVG barcode using python-barcode or pure python fallback."""
    if not code_str:
        return ""
    try:
        import barcode
        from barcode.writer import SVGWriter
        rv = io.BytesIO()
        code128 = barcode.get('code128', str(code_str), writer=SVGWriter())
        code128.write(rv, options={
            'module_height': 10.0,
            'module_width': 0.25,
            'font_size': 9,
            'text_distance': 3.0,
            'write_text': True
        })
        svg = rv.getvalue().decode('utf-8')
        if '<svg' in svg:
            svg = svg[svg.find('<svg'):]
        return svg
    except Exception:
        return generate_code128_svg_fallback(str(code_str))
