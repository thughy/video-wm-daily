// 手机端（≤600px）：长段落默认折叠，「与已有工作的区别」不折叠（构建时就没有包成可折叠块）
(function () {
  if (!window.matchMedia || !window.matchMedia("(max-width: 600px)").matches) return;
  document.querySelectorAll("details.fold[open]").forEach(function (d) {
    if (location.hash && d.closest(location.hash)) return; // 直接跳到某张卡时保持展开
    d.removeAttribute("open");
  });
})();
