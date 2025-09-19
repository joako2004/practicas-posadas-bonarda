// Animación del botón al cargar
document.addEventListener('DOMContentLoaded', ()=>{
  const btn = document.querySelector('.cta-hero');
  if(btn){
    setTimeout(()=>{
      btn.style.transition = 'transform 600ms cubic-bezier(.2,.9,.2,1), opacity 600ms';
      btn.style.transform = 'translateY(0)';
      btn.style.opacity = '1';
    },200);
  }
});