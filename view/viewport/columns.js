var myCodeMirror;
var spaceMarkings;
var updateEventUserHandler;
var viewportIsDisabled; 

function createViewport(text, firstLineNumber, userHandler) {
    // NOTE: updateEventUserHandler() will be run every time after columnize()

    /*$(".word").each(function(index) {
            console.log("["+index+"]("+$(this).html()+"): " + $(this).width());
    });*/

    myCodeMirror = CodeMirror(/*document.getElementById("viewport")*/document.body, {
        value: text,
        mode:  "vertmode", 
        lineNumbers: true, 
        firstLineNumber: firstLineNumber, 
        //height: "auto", 
        viewportMargin: Infinity,  // automatically resize viewport to fit its content
        scrollbarStyle: "null", 
        styleActiveLine: true
    });

    spaceMarkings = new Array();
    columnize();

    updateEventUserHandler = userHandler;
    //updateEventUserHandler();

    // register event handler
    updateEventSetEnabled(true);

    return myCodeMirror;
}


function disableViewport() {
    myCodeMirror.getWrapperElement().style.visibility = 'hidden';
    viewportIsDisabled = true;
}
function enableViewport() {
    myCodeMirror.getWrapperElement().style.visibility = 'visible';
    viewportIsDisabled = true;
}


function updateEventSetEnabled(isEnabled) {
    if (isEnabled) 
        myCodeMirror.on("update", updateEventHandler);
    else 
        myCodeMirror.off("update", updateEventHandler);
}

var columnizeTimer;
function updateEventHandler() {
    /////console.log("event occured: update.");
    updateEventSetEnabled(false);

    // schedule columnization; it won't be done in the middle of typing (every change resets the timer)
    clearTimeout(columnizeTimer);
    columnizeTimer = setTimeout(runColumnize, 1000);  // delay of no change until runColumnize() is run: 1000 ms
    
    //columnize();
    updateEventSetEnabled(true);
}

function runColumnize() {
    disableViewport();

    clearTimeout(columnizeTimer);
    updateEventSetEnabled(false);
    columnize();
    updateEventSetEnabled(true);

    // run the additional, user-supplied handler function
    updateEventUserHandler();

    enableViewport();
}


function getColWidths(minimumSpaceWidth) {
    // -- determine how wide each column needs to be --

    var text = myCodeMirror.getValue();
    var lines = text.split("\n");
    var colMaxWidth = new Array();  // array containing the width (in pixels) of the widest word for each column
    var i;

    for (i = 0; i < lines.length; i++) {
        /////console.log("line: " + lines[i]);
        var c;
        var wordI = -1;
        for (c = 0; c < lines[i].length; c++) {
            var WHITESPACE_MAX_CHARCODE = 32;
            if (!(lines[i].charCodeAt(c) <= WHITESPACE_MAX_CHARCODE)) { // non-whitespace character (word) -> measure
                wordI++;

                /////console.log("word {");
                /////console.log("'"+lines[i][c]+"' ("+lines[i].charCodeAt(c)+")");

                // remember where the word begins
                var beginC = c;

                // go to the next whitespace or to the end of the line
                do { 
                    c++; 
                    if (!(c < lines[i].length)) break;
                    /////console.log("'"+lines[i][c]+"' ("+lines[i].charCodeAt(c)+")");
                } while (!(lines[i].charCodeAt(c) <= WHITESPACE_MAX_CHARCODE));

                // measure the width of the word
                var wordWidth = distance(i, beginC, c);

                /////console.log("} width: " + wordWidth);
                
                // record the width
                /////console.log("===> wordI, colMaxWidth.length, colMaxWidth: " + 
                /////        wordI, colMaxWidth.length, colMaxWidth);
                if (wordI < colMaxWidth.length) { // an existing column
                    if (wordWidth > colMaxWidth[wordI]) { // this word is so far the widest in this column
                        colMaxWidth[wordI] = wordWidth;
                    }
                } else { // a new column
                    colMaxWidth.push(wordWidth);
                }
            }
        }
    }

    // finally, extend each column by the minimum space width 
    // (otherwise each column would be just as wide as its widest word, with no room for space)
    for (var i = 0; i < colMaxWidth.length; i++) {
        colMaxWidth[i] += minimumSpaceWidth;
    }

    /////console.log("colMaxWidth: " + colMaxWidth);
    return colMaxWidth;
}


function distance(line, ch1, ch2) {
    // -- measure distance between two characters --
    var beginX = myCodeMirror.charCoords({line: line, ch: ch1}).left;
    var endX = myCodeMirror.charCoords({line: line, ch: ch2}).left;
    return (endX - beginX);
}


function makeColumnView(colWidths) {
    // -- adjust the width of the spaces to make a column view --

    // clear the old markings
    for (var i = 0; i < spaceMarkings.length; i++) {
        spaceMarkings[i].clear();
    }

    // empty the stylesheet
    var stylesheet = document.getElementById("space-markings-stylesheet");
    while (stylesheet.firstChild) {
        stylesheet.removeChild(stylesheet.firstChild);
    }

    var text = myCodeMirror.getValue();
    var lines = text.split("\n");
    var i;
    var classNameI = 0;

    for (i = 0; i < lines.length; i++) {
        /////console.log("line: " + lines[i]);

        if (lines[i].length > 0 && lines[i][0] == "<") {
            // don't adjust spaces if the line is a tag
            continue;
        }

        var c;
        var lastWordI = -1;

        for (c = 0; c < lines[i].length; c++) {
            var WHITESPACE_MAX_CHARCODE = 32;
            if (lines[i].charCodeAt(c) <= WHITESPACE_MAX_CHARCODE) { // whitespace character (space)
                if (lastWordI >= 0) {
                    /////console.log("space {");

                    // remember where the space begins
                    var beginC = c;

                    // go to the next non-whitespace character or to the end of the line
                    do { 
                        /////console.log("'"+lines[i][c]+"' ("+lines[i].charCodeAt(c)+")");
                        c++; 
                        if (!(c < lines[i].length)) break;
                    } while (lines[i].charCodeAt(c) <= WHITESPACE_MAX_CHARCODE);
                    c--;

                    // remember where the space ends (index of the first character after it)
                    var endC = c + 1;
                    /////console.log("} ("+beginC+", "+endC+")");

                    // mark the space so that it is displayed with the correct width 
                    var className = "adjusted-space" + classNameI; classNameI++;

                    var spaceWidth = distance(i, beginC, endC);
                    /////console.log("---> lastWordI, lastWordWidth, colWidths[lastWordI]: " + 
                    /////        lastWordI + ", " + lastWordWidth + ", " + colWidths[lastWordI]);
                    var adjustedSpaceWidth = colWidths[lastWordI] - lastWordWidth; 

                    stylesheet.innerHTML += "." + className + 
                        "{/*background-color: lime;*/ width: " + adjustedSpaceWidth + "px}\n";
                    var marking = myCodeMirror.markText({line: i, ch: beginC}, 
                            {line: i, ch: endC}, {className: className});

                    // save the marking so that it can be cleared later
                    spaceMarkings.push(marking);
                }

            } else {  // other character (word)
                lastWordI++;
                /////console.log("["+lastWordI+"] word {");

                // remember where the word begins
                var beginC = c;

                // go to the next whitespace or to the end of the line
                do { 
                    /////console.log("'"+lines[i][c]+"' ("+lines[i].charCodeAt(c)+")");
                    c++; 
                    if (!(c < lines[i].length)) break;
                } while (!(lines[i].charCodeAt(c) <= WHITESPACE_MAX_CHARCODE));
                c--;

                // remember where the word ends (index of the first character after it)
                var endC = c + 1;

                // measure the word to be able to tell later how wide the space after it needs to be
                lastWordWidth = distance(i, beginC, endC);
                /////console.log("} width: " + lastWordWidth);
            }
        }

    }
}


function columnize() {
    console.log("columnizing...");
    /*
    var wds = document.getElementsByClassName("cm-tab"); 
    var i;
    for (i = 0; i < wds.length; i++) {
        //...
    }*/
    /* This above is a wrong approach, it violates encapsulation. I should NOT directly 
       mess with the way the elements in the area are displayed, that is essentially 
       a private thing of CodeMirror and should be left under CodeMirror's control. 
       Changing the sizes of the spaces between words this way can break it.

       The correct way: do everything through CodeMirror's interface.

       CodeMirror's API doesn't seem to provide a way to style parts of the text 
       outside of the styling done by the mode. But addons can do that. See especially 
       merge/merge.js. Demo: http://codemirror.net/demo/merge.html
       BTW this addon is going to be useful later for conflict resolution UI.

       *** UPDATE: found the solution! ***
       The addon selection/mark-selection.js does what we need: apply a custom 
       style to a part of the text. Demo: http://codemirror.net/demo/markselection.html
       With this addon, I will safely adjust the sizes of the spaces between words.

       *** UPDATE2: CodeMirror's API in fact does provide a way to style a part of the text ***
       http://codemirror.net/doc/manual.html#markText
       mark-selection.js uses it.
       NOTE: We will need to dynamically create the style for each space.
     */

    var colWidths = getColWidths(20); // there will be at least 20px space between any two words
    console.log("###> colWidths: " + colWidths);
    makeColumnView(colWidths);
}


