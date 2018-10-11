//JavaScript code to upload song files

//var globalbird = {};

function successfunction(res) {
    d3.select('.busysignal').attr("style", "display:none");
    json = JSON.parse(res);
    reportresult(json);
}

function errorfunction(res) {
    d3.select('.busysignal').attr("style", "display:none");
    console.log("Error");
    console.log(res);
}

function upload() {
    d3.select('.busysignal').attr("style", "display:inline");
    //var form = $('#uploadform');
    //var form = document.getElementById('uploadform');
    //var formdata = new FormData(form);
    var fileinput = document.getElementById('userfile');
    var formdata = new FormData();
    formdata.append('userfile', fileinput.files[0]);
    $.ajax({
	type: "POST",
	url: "upload.php?method=upload",
	data: formdata,
	processData: false,
	contentType: false,
	cache: false,
	success: function(res) {
	    successfunction(res);
	},
	error: function(res) {
	    errorfunction(res);
	}
    });
}

function copyurl() {
    d3.select('.busysignal').attr("style", "display:inline");
    $.ajax({
	type: "POST",
	url: "upload.php?method=copyurl&url=" + $('#text').val(),
	success: function(res) {
	    successfunction(res);
	},
	error: function(res) {
	    errorfunction(res);
	}
    });
}

function example() {
    d3.select('.busysignal').attr("style", "display:inline");
    $.ajax({
	type: "POST",
	url: "upload.php?method=example&filename=" + $('#select').val(),
	success: function(res) {
	    successfunction(res);
	},
	error: function(res) {
	    errorfunction(res);
	}
    });
}

function reportresult(json) {
    newrows = d3.select('#ranktable').selectAll("tr")
	.data(json)
	.enter()
	.append("tr")
    newrows.append("td").attr("class","col0");
    newrows.append("td").attr("class","col1").append("a").attr("class","birdanchor").attr("target","_blank").append("img").attr("class","birdpicture").attr("width",100);
    newrows.append("td").attr("class","col2");
    newrows.append("td").attr("class","col3");
    newrows.append("td").attr("class","col4");
    c5 = newrows.append("td").attr("class","col5");
    c5.append("a").attr("class","wikipedia_link").attr("target","_blank").append("img").attr("src","links/wikipedia.png");
    c5.append("a").attr("class","xenocanto_link").attr("target","_blank").append("img").attr("src","links/xenocanto.png");
    c5.append("a").attr("class","audubon_link").attr("target","_blank").append("img").attr("src","links/audubon.png");
    d3.selectAll(".col0").data(json).text(function(d,i){
	return i+1;
    });
    d3.selectAll(".birdanchor").data(json).attr("href", function(d,i){
	return "bird_photos/" + d["genus"] + "_" + d["species"] + ".jpg";
    });
    d3.selectAll(".birdpicture").data(json).attr("src", function(d,i){
	return "bird_photos/" + d["genus"] + "_" + d["species"] + ".jpg";
    });
    d3.selectAll(".col2").data(json).text(function(d,i){
	return d["common name"];
    });
    d3.selectAll(".col3").data(json).text(function(d,i){
	return d["scientific name"];
    });
    d3.selectAll(".col4").data(json).text(function(d,i){
	return (d["probability"]*100).toFixed(1) + '%';
    });
    d3.selectAll(".wikipedia_link").data(json).attr("href", function(d,i){
	return "https://en.wikipedia.org/wiki/" + d["genus"] + "_" + d["species"];
    });
    d3.selectAll(".xenocanto_link").data(json).attr("href", function(d,i){
	return "https://www.xeno-canto.org/species/" + d["genus"] + "-" + d["species"];
    });
    d3.selectAll(".audubon_link").data(json).attr("href", function(d,i){
	nameformatted = d["common name"].toLowerCase().replace(/ /g, "-").replace(/'/g, "");
	return "https://www.audubon.org/field-guide/bird/" + nameformatted;
    });
    d3.select('table.results').attr("style", "display:inline");
    d3.select('.busysignal').attr("style", "display:none");
}
