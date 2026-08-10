(() => {
  window.addEventListener('pageshow', (event) => {
    if (event.persisted) window.location.reload();
  });

  const siteNav = document.querySelector('#site-nav');
  const nav = document.querySelector('.nav');
  if (!siteNav || !nav) return;

  const page = nav.dataset.sitePage || 'home';
  const isHome = page === 'home';
  const toHomeSection = (id) => isHome ? `#${id}` : `index.html#${id}`;
  const createLink = (label, href, { active = false, current = false } = {}) => {
    const link = document.createElement('a');
    link.textContent = label;
    link.href = href;
    if (active) link.classList.add('active');
    if (current) link.setAttribute('aria-current', 'page');
    return link;
  };
  const createDisplay = (label, className) => {
    const item = document.createElement('span');
    item.textContent = label;
    item.className = className;
    item.setAttribute('aria-disabled', 'true');
    return item;
  };

  const navigation = [
    { key: 'home', label: '首页', href: toHomeSection('home'), hasPage: true },
    { key: 'major', label: '专业建设中心', submenuLabel: '专业建设中心二级菜单', children: [['专业设置'], ['专业群建设'], ['专业资源库'], ['人才培养方案', 'talent-training.html', 'talent-training'], ['微专业'], ['校企协同育人项目']] },
    { key: 'course', label: '课程教学中心', submenuLabel: '课程教学中心二级菜单', children: [['思政门户'], ['课程中心', 'course.html', 'course']] },
    { key: 'resource', label: '教材资源中心', submenuLabel: '教材资源中心二级菜单', children: [['智能教学资源制作中心'], ['教材资源库', 'textbook-resources.html', 'textbook-resources'], ['教材成果库', 'textbook-achievements.html', 'textbook']] },
    { key: 'teacher', label: '教师发展中心', href: 'teacher-development.html', hasPage: true },
    { key: 'practice', label: '实践教学中心', submenuLabel: '实践教学中心二级菜单', children: [['毕业设计'], ['实习实训'], ['技能大赛'], ['虚拟仿真']] },
    { key: 'data', label: '教学大数据中心' },
    { key: 'ai', label: 'AI能力中心', submenuLabel: 'AI能力中心二级菜单', children: [['AI工具'], ['教师智能体成果']] }
  ];

  const activeGroup = page === 'textbook' || page === 'textbook-resources'
    ? 'resource'
    : page === 'talent-training'
      ? 'major'
      : page;
  const items = navigation.map((entry) => {
    const item = document.createElement('div');
    item.className = 'nav-item';
    if (!entry.children) {
      const label = entry.hasPage
        ? createLink(entry.label, entry.href, { active: entry.key === activeGroup, current: entry.key === page })
        : createDisplay(entry.label, 'nav-link nav-link--static');
      label.classList.add('nav-link');
      item.append(label);
      return item;
    }

    item.classList.add('has-submenu');
    const parent = createDisplay(entry.label, 'nav-link nav-link--static');
    if (entry.key === activeGroup) parent.classList.add('active');
    const submenu = document.createElement('div');
    submenu.className = 'submenu';
    submenu.setAttribute('aria-label', entry.submenuLabel);
    entry.children.forEach(([label, destination, childPage]) => {
      if (!destination) {
        submenu.append(createDisplay(label, 'submenu-static'));
        return;
      }
      submenu.append(createLink(label, destination, { active: childPage === page, current: childPage === page }));
    });
    item.append(parent, submenu);
    return item;
  });
  siteNav.replaceChildren(...items);

  const brand = nav.querySelector('.brand');
  const login = nav.querySelector('.login');
  if (brand) brand.href = toHomeSection('home');
  if (login) login.href = toHomeSection('login');
})();
