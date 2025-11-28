document.addEventListener("scroll", () => {
  const navbar = document.getElementById("navbar");
  navbar.classList.toggle("scrolled", window.scrollY > 80);
});
