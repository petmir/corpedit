if (typeof Promise !== "undefined") {
  var comp = [
    ["here", "hither"],
    ["asynchronous", "nonsynchronous"],
    ["completion", "achievement", "conclusion", "culmination", "expirations"],
    ["hinting", "advive", "broach", "imply"],
    ["function","action"],
    ["provide", "add", "bring", "give"],
    ["synonyms", "equivalents"],
    ["words", "token"],
    ["each", "every"],
  ]

  function synonyms(cm, option) {
    return new Promise(function(accept) {
      //setTimeout(function() {
        var cursor = cm.getCursor(), line = cm.getLine(cursor.line);
        var start = cursor.ch, end = cursor.ch;
        while (start && /\w/.test(line.charAt(start - 1))) --start;
        while (end < line.length && /\w/.test(line.charAt(end))) ++end;

        // TODO: better detection of context
        if (start == 0) {
            // first char of the line -> offer nothing
            //alert('nothing');
            return accept(null);
        } else if ((line.charAt(0) == '<' && start == 1) ||
                   (line.charAt(0) == '<' && line.charAt(start - 1) == '/')) {
            // offer structural tag names
            //alert('structural tag');
            //items = ["tag1", "tag2", "tag3"]
        } else if (line.charAt(0) == '<' && line.charAt(start - 1) == ' ') {
            // offer attribute names for this structural tag
            //alert('attribute name of structural tag');
            
            var word = line.slice(start, end).toLowerCase();
            //alert('.'+word+'.');

            var xhr = new XMLHttpRequest();
            var wid = document.getElementById("window_id").innerHTML;
            // TODO: send tag name so that we get only attributes for it, not for other tags
            var url = 'cgicontroller.cgi?a=ajax_get_suggestions&wordtype=structattr&word=N' + word + '&wid=' + wid;
            xhr.open('GET', url);
            xhr.onload = function () {
                var response = JSON.parse(xhr.response);
                //alert(response.suggestions);
                accept({list: response.suggestions,
                        from: CodeMirror.Pos(cursor.line, start),
                        to: CodeMirror.Pos(cursor.line, end)});
            }
            xhr.send();
            //items = ["attrname1", "attrname2", "attrname3"]*/
        } /*else if (line.charAt(0) == '<' && line.charAt(start - 1) == '"') {
            // offer attribute values for this structural tag and attribute
            alert('value of attribute of structural tag');
            items = ["attrval1", "attrval2", "attrval3"]
        }*/ else {
            // some word, possibly a morphological attribute -> offer values
            //alert('other word, possibly a morphological attribute');
            //var word = line.slice(start, end).toLowerCase();
            var word = line.charAt(cursor.ch - 1);
            //alert(word);

            var xhr = new XMLHttpRequest();
            var wid = document.getElementById("window_id").innerHTML;
            var url = 'cgicontroller.cgi?a=ajax_get_suggestions&wordtype=morphattr&word=' + word + '&wid=' + wid;
            xhr.open('GET', url);
            xhr.onload = function () {
                var response = JSON.parse(xhr.response);
                //alert(response.suggestions);
                accept({list: response.suggestions,
                        from: CodeMirror.Pos(cursor.line, cursor.ch - 1),
                        to: CodeMirror.Pos(cursor.line, cursor.ch + 1)});
            }
            xhr.send();
        }



        /*for (var i = 0; i < comp.length; i++) {
            return accept({list: items,
                           from: CodeMirror.Pos(cursor.line, start),
                           to: CodeMirror.Pos(cursor.line, end)});
        }
        return accept(null);*/

      //}, 100)
    })
  }

  /*var editor2 = CodeMirror.fromTextArea(document.getElementById("synonyms"), {
    extraKeys: {"Ctrl-Space": "autocomplete"},
    lineNumbers: true,
    lineWrapping: true,
    mode: "text/x-markdown",
    hintOptions: {hint: synonyms}
  })*/
}
