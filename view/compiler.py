def compile_template(template_file, data):
    """
    Naplni sablonu daty a vysledek vrati jako retezec.
    """
    from cStringIO import StringIO
    output_stream = StringIO()

    import xyaptu
    xcp = xyaptu.xcopier(data, ouf=output_stream)
    xcp.xcopy(template_file)

    output = output_stream.getvalue()
    return output
