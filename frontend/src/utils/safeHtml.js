/**
 * 安全 HTML 工具：将 LLM/用户输入产生的 HTML 在通过 v-html 渲染前
 * 用 DOMPurify 过滤，移除 <script>/onerror 等危险片段，避免 XSS。
 *
 * 设计要点：
 * - 仅放行 Markdown 渲染器实际生成的标签集（白名单），减小攻击面
 * - 允许少量 data-* 属性（renderMarkdown 用 data-level 表达列表层级）
 * - 不允许任何事件处理属性（on*），不允许 javascript: 协议
 */

import DOMPurify from 'dompurify'

const ALLOWED_TAGS = [
  'a', 'b', 'blockquote', 'br', 'code', 'div', 'em',
  'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
  'hr', 'i', 'li', 'ol', 'p', 'pre', 'span', 'strong',
  'sub', 'sup', 'table', 'tbody', 'td', 'th', 'thead', 'tr', 'ul'
]

const ALLOWED_ATTR = ['class', 'href', 'title', 'data-level', 'target', 'rel']

/**
 * 净化 HTML 字符串，可安全地传递给 v-html。
 * @param {string} dirty 待净化的 HTML
 * @returns {string} 净化后的 HTML（绝不会包含可执行脚本）
 */
export function sanitizeHtml(dirty) {
  if (dirty == null) return ''
  return DOMPurify.sanitize(String(dirty), {
    ALLOWED_TAGS,
    ALLOWED_ATTR,
    // 强制移除任何 on* 事件处理属性（DOMPurify 默认即如此，显式声明以防配置漂移）
    FORBID_ATTR: ['style', 'onerror', 'onload', 'onclick'],
    // 拒绝 javascript: / data: 协议的 href
    ALLOW_UNKNOWN_PROTOCOLS: false,
  })
}

export default sanitizeHtml
