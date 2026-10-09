(function(){
  var st={dir:'all',rating:'all'};
  function apply(){
    var days=document.querySelectorAll('ol.days>li'),shown=0,active=st.dir!=='all'||st.rating!=='all';
    days.forEach(function(d){
      var n=0;
      d.querySelectorAll('ul.dp>li').forEach(function(p){
        var ok=(st.dir==='all'||(' '+p.dataset.dirs+' ').indexOf(' '+st.dir+' ')>=0)&&(st.rating==='all'||p.dataset.rating===st.rating);
        p.style.display=ok?'':'none';if(ok)n++;
      });
      var vis=!active||n>0;d.style.display=vis?'':'none';if(vis)shown++;
    });
    var nr=document.querySelector('.noresult');if(nr)nr.style.display=shown?'none':'block';
  }
  document.querySelectorAll('.filters button').forEach(function(b){
    b.addEventListener('click',function(){
      var k=b.dataset.k;st[k]=b.dataset.v;
      document.querySelectorAll('.filters button[data-k="'+k+'"]').forEach(function(x){x.setAttribute('aria-pressed',x===b?'true':'false')});
      apply();
    });
  });
})();
