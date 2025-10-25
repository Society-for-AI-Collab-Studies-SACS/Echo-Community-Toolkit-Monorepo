(() => {
  // Enhance flags rendering and chapter list if needed
  const flagsNodes = document.querySelectorAll('.flags');
  flagsNodes.forEach((node) => {
    const text = node.textContent || '';
    const match = text.match(/\[Flags:\s*([^\]]+)\]/i);
    if (match) {
      const parts = match[1].split(',').map((s) => s.trim());
      node.setAttribute('data-flags', parts.join(' | '));
    }
  });

  // If on index, ensure chapter list exists even if files not yet generated
  const list = document.querySelector('#chapters-list');
  if (list && list.children.length === 0) {
    for (let i = 2; i <= 20; i++) {
      const li = document.createElement('li');
      const a = document.createElement('a');
      a.href = `chapter${String(i).padStart(2, '0')}.html`;
      a.textContent = `Chapter ${String(i).padStart(2, '0')}`;
      li.appendChild(a);
      list.appendChild(li);
    }
  }
})();

