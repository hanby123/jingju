// 京剧数据可视化竞赛 - 项目网站主 JS

document.addEventListener('DOMContentLoaded', function() {
    // Flash 消息自动消失
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(msg => {
        setTimeout(() => {
            msg.style.opacity = '0';
            msg.style.transform = 'translateY(-8px)';
            msg.style.transition = 'all 0.3s ease';
            setTimeout(() => msg.remove(), 300);
        }, 4000);
    });

    // 导航栏活动状态
    const currentPath = window.location.pathname;
    document.querySelectorAll('.nav-menu a').forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.style.background = 'rgba(180, 145, 85, 0.15)';
            link.style.color = '#b87a3c';
        }
    });
});
