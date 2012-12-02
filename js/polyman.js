// JavaScript Document
//add prototype function panToWithOffset
String.prototype.capitalize = function() {
			var textString = this.split(" ");
			var newstring = [];
			for(var t=0; t<textString.length; t++){
				newstring.push(textString[t].charAt(0).toUpperCase() + textString[t].slice(1))
			}
			return newstring.join(" ");
		}
google.maps.Map.prototype.panToWithOffset = function(latlng, offsetX, offsetY) {
    var ov = new google.maps.OverlayView(); 
    ov.draw = function() {}; 
    ov.setMap(this); 
    var proj = ov.getProjection();

    var aPoint = proj.fromLatLngToContainerPixel(latlng);
    aPoint.x = aPoint.x+offsetX;
    aPoint.y = aPoint.y+offsetY;
    this.panTo(proj.fromContainerPixelToLatLng(aPoint));
}
//extend the google.maps.Polygon class
google.maps.Polygon.prototype.getBounds = function() {//returns the bounds of the selected Polygon
		var bounds = new google.maps.LatLngBounds();
		var paths = this.getPaths();
		var path;        
		for (var i = 0; i < paths.getLength(); i++) {
			path = paths.getAt(i);
			for (var ii = 0; ii < path.getLength(); ii++) {
				bounds.extend(path.getAt(ii));
			}
		}
		return bounds;
}
	
google.maps.Polygon.prototype.getID = function(){// return the id of the Polygon as defined by polyID
	return this.polyID;
}

google.maps.Polygon.prototype.getContent = function(){// return the content for the polygon
	return this.polyHTML;
}


/* this class manages layers placed on the map. the class accepts a javascript object with configurations. */
var Polyman = function(config){ 
	/*This polylinks property holds the urls for given polygon types */
	this.polylinks = {
		"county":"../demo/json/test.geojson", // url for the county layer
		"constituency":"../demo/json/Constitest.geojson", // url for the constituency layer
		"ward":"" // url for the ward layer
	};
	
	this.hidden = true;
	/*this holds the map that the layer is for*/
	if(config.map){
		this.map = config.map
	}
	
	if(config.type){
		this.url = this.polylinks[config.type]; //this is the url to the polygon coordinates.
		this.type = config.type //this sets the layer type. county, constituency or ward
	}
	else{
		this.url = this.polylinks["county"]// if no type is specified in config, load county by default
		this.type = "county" //defaults the layer type to county if config.type is not set
	}
	
	this.polyArray = [] //this array will hold all the polygons that will consist this layer
	this.selectedPolygons = [] //this holds the polygons that have been selected.
	this.hoveredPolygons = [] //this holds the polygons that have been hovered on.
	/* the fetchPolygons method of the Polyman class handles the fetching of the polygons and stores them in the polyArray */
	this.fetchPolygons = function(){
		var polyArray = []
		var polyType = this.type;
		$.ajax({
			url: this.url,
		    async: false,
			dataType: "json",
			success: function(json){
				polyLayer = json.features
				$.each(polyLayer, function(p, polygon){
					if(polyType=="county"){
						var polygonName = polygon.properties.COUNTY;
						var polygonID = polygon.properties.COUNTY3_ID;
					}
					else if(polyType=="constituency"){
						var polygonName = polygon.properties.CONSTITUEN;
						var polygonID = polygon.properties.CONST_CODE;
					}
					var polygonCoordsArray = polygon.geometry.coordinates;
					var polygonType = polygon.geometry.type;
					var path = []
					if(polygonType=="Polygon"){
						$.each(polygonCoordsArray, function(c, coords){
							$.each(coords, function(pc, pcoords){
								path.push(new google.maps.LatLng(pcoords[1], pcoords[0]))
							})
						});
					}
					else{
						$.each(polygonCoordsArray, function(c, coords){
							var partPath = [];
							$.each(coords, function(pc, pcoords){
								$.each(pcoords, function(ar, arcoords){
									partPath.push(new google.maps.LatLng(arcoords[1], arcoords[0]))
								});
								path.push(partPath)
							})
						});
					}
					var polygonOptions = {
						polyHTML: "No Content Available",
						polyID: polygonID,
						polyName: polygonName,
						strokeColor: "#111",
						paths: path,
						fillOpacity:0,
						strokeOpacity:0,
						strokeWeight: 1
					}
					polyArray.push(new google.maps.Polygon(polygonOptions))
				});
			}			
		});
		this.polyArray = polyArray;
	}
	/*This method of the Polygon class populates the polygon's polyHTML property with the right content */
	this.setContent = function(content, poly){
		poly.setOptions({
			polyHTML: content
		})
	}
	
	/*this method is used to make the polygons in the polyArray visible */
	this.show = function(map, animate){
		var polArrs = this.polyArray;
		var polyType = this.type;
		var selectedPolygons = this.selectedPolygons;
		var hoveredPoly = this.hoveredPolygons;
		var opac = 0;
		$.each(polArrs, function(i, val){
			val.setOptions({
				polyHTML: "<div class='layer-window'>"+val.polyName+" "+polyType.capitalize()+"</div>"
			})
			var myOptions = {
						disableAutoPan: true
						,maxWidth: 0
						,pixelOffset: new google.maps.Size(5, 10)
						,zIndex: null
						,boxStyle: { 
						  opacity: 0.95
						  ,width: "auto"
						 }
                		,closeBoxURL: ""
						,infoBoxClearance: new google.maps.Size(1, 1)
						,isHidden: false
						,pane: "floatPane"
						,enableEventPropagation: false
				};

				var infoBox = new InfoBox(myOptions)
			//Add position changed event Listener to the infoBox
			
			google.maps.event.addListener(infoBox, 'position_changed', function(event){
				this.getContent(this.getContent()+" position Lat")
			})
			
			//The event Listener below configures the polygon on click behavior
			google.maps.event.addListener(val, 'click', function(event){
				var polyID = this.getID()
				//Unselect previously selected polygons//
				$.each(selectedPolygons, function(s, selected){
					selected.setOptions({strokeWeight:1, strokeColor:"#111"})
					selectedPolygons = []//Clear the Array
				})
				map.fitBounds(val.getBounds())
				this.setOptions({strokeWeight:1, strokeColor:"#038"})
				selectedPolygons.push(this);
			})
			
			//The event Listeners below configure the Polygon Behavior on Hover
			google.maps.event.addListener(val, 'mouseover', function(event){
				infoBox.open(map)
				infoBox.setContent(this.getContent())
				if(selectedPolygons.length > 0){//Test whether there are any polygons currently selected
					if(this.polyID != selectedPolygons[0].polyID){
						this.setOptions({strokeWeight:1, strokeColor:"#28E81E"})
						hoveredPoly.push(this)
					}
				}
				else{
					this.setOptions({strokeWeight:1, strokeColor:"#28E81E"})
					hoveredPoly.push(this)
				}
			})
			google.maps.event.addListener(val, 'mousemove', function(event){
				infoBox.setPosition(event.latLng)
			})
			google.maps.event.addListener(val, 'mouseout', function(event){
				infoBox.close()
				if(selectedPolygons.length > 0){ //Test whether there are any polygons currently selected
					if(this.polyID != selectedPolygons[0].polyID){
						this.setOptions({strokeWeight:1, strokeColor:"#111"})
						hoveredPoly = []
					}
				}
				else{
					this.setOptions({strokeWeight:1, strokeColor:"#111"})
					hoveredPoly = []
				}
			})
			if(animate==true){
				$('#layerinfo').append('<br /> '+opac)
				var animator = setInterval(function(){
					if(val.strokeOpacity<=0.6){
						val.setOptions({strokeOpacity:opac, fillOpacity:opac})
						$('#layerinfo').append('<br /> '+opac)
					}
					else{
						clearInterval(animator)
					}
					opac += 0.003
				},100)
			}
			else{
				val.setOptions({strokeOpacity:0.6, fillOpacity:0})
			}
			val.setMap(map)
		});
		this.selectedPolygons = selectedPolygons; //store the newly selected polygon into the Array
		this.hoveredPolygons = hoveredPoly;// store the polygon being hovered on into the Array
		this.hidden = false;
	}
	this.animateShow = function(opacity){
		$.each(this.polyArray, function(p, poly){
			poly.setOptions({strokeOpacity:opacity, fillOpacity:opacity})
		});
		if(opacity >= 0.7){
			return true;
		}
		else{
			return false;
		}
	}
	/*this method is used to make the polygons in the polyArray hidden */
	this.hide = function(){
		var polArrs = this.polyArray;
		$.each(polArrs, function(i, val){
			google.maps.event.clearListeners(val, 'click')
			$('#layerinfo').html("")
			val.setMap(null)
		});
	}
	this.fetchPolygons()
	this.hidden = true;
	this.setOptions = function(ops){
		$.each(this.polyArray, function(p, poly){
			poly.setOptions(ops)
		});
	}
	this.contains = function(loc){
		thePolies = this.polyArray;
		parent = "";
		for(var p=0; p<thePolies.length; p++){
			if(thePolies[p].containsLatLng(loc)){
				parent = thePolies[p].polyName
			}
		}
		return parent
	}
}