var Include={
	myModule: function(element,success){
		typeof success == 'undefined' ? success = function(){} : success = success;
		Include.unconditionedLauncher(['modules/'+element+'/'+element+'.js','modules/'+element+'/'+element+'.css'],function(){success('Module ready');});		
	},

	myScript: function(element,success){
		typeof success == 'undefined' ? success = function(){} : success = success;
		Include.unconditionedLauncher(element,function(){success('Scripts ready')});
	},

	unconditionedLauncher: function(element,success){
		yepnope({    
		    load : element, 
		    complete  : function(){		      
		       success();
		    }        
		});
	},

	conditionedLauncher: function(yepElements,nopeElements,condition,success){
		yepnope({  
		    test : condition,  
		    yep : yepElements,
		    nope : nopeElements, 
		    complete  : function(){  		      
		       success('ready');
		    }        
		});
	}
}