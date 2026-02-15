



const hostElement = document.querySelector('#uMtSJ0 > div > div');
console.log(hostElement);
const ifr = hostElement .getElementsByTagName('iframe');
console.log(ifr);
const shadowRoot = hostElement.shadowRoot;
console.log(shadowRoot);
iframe = hostElement.querySelector('iframe[title="包含 Cloudflare 安全质询的小组件"]')
console.log(iframe);
iframe = shadowRoot.querySelector('iframe[title="包含 Cloudflare 安全质询的小组件"]');
if (!iframe) return null;
console.log(iframe);
return iframe;