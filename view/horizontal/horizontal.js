var horizontalUpdateHandler;

function setHorizontalUpdateHandler(f) {
    horizontalUpdateHandler = f;
}

$(function  () {
  var group = $("ol.serialization").sortable({
    group: 'serialization',
    delay: 500,
    onDrop: function ($item, container, _super) {
      /*var data = group.sortable("serialize").get();

      var jsonString = JSON.stringify(data, null, ' ');

      $('#serialize_output2').text(jsonString);
      _super($item, container);

      // moje:

      numItems = JSON.parse(jsonString)[0].length;
      for (i = 0; i < numItems; i++) {
          alert(JSON.parse(jsonString)[0][i].id);
      }*/

      _super($item, container);

      var data = group.sortable("serialize").get();
      horizontalUpdateHandler(data);
      //numItems = data[0].length;
      //alert(numItems);
      //for (i = 0; i < numItems; i++) {
      //    alert(data[0][i].id);
      //}
    }
  });
});
