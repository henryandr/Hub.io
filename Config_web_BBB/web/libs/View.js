var View ={

	render:function(name,target,data,success){
        typeof success == 'undefined' ? success = function(){} : success = success;
		View.htmlCall(name,target,data,false,success);
	},

	render_append:function(name,target,data,success){
        typeof success == 'undefined' ? success = function(){} : success = success;
		View.htmlCall(name,target,data,true,success);
	},

	htmlCall:function(name,target,data,append,success){		
		$.ajax(
        {
            url: 'modules/'+name+'.html',
            async: true,
            success:function(html_page){
            	var to_render = html_page;
            	if (data){
            		to_render = Mustache.render(html_page, data);
            	}
            	if(append){
            		$(target).append(to_render);
            	}else{
            		$(target).html(to_render);
            	}
            	success('Success');
        	},
        	error:function(msgError){
        		success('Error');
        	}
        });
	}
}