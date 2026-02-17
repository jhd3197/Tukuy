/**
 * Tukuy HTML Transformers — JS port
 *
 * Ports of tukuy/plugins/html Python transformers.
 * Uses regex for universal (browser + Node) compatibility.
 * No external dependencies (no BeautifulSoup equivalent needed).
 */

export const htmlTransformers = [
  {
    name: 'strip_html_tags',
    displayName: 'Strip HTML Tags',
    description: 'Remove all HTML tags, keep text content',
    category: 'html',
    inputType: 'string',
    outputType: 'string',
    params: [],
    transform(input) {
      // Remove script/style content entirely, then strip remaining tags
      let text = String(input);
      text = text.replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, '');
      text = text.replace(/<style\b[^>]*>[\s\S]*?<\/style>/gi, '');
      text = text.replace(/<[^>]+>/g, '');
      // Collapse whitespace and decode common entities
      text = text
        .replace(/&amp;/g, '&')
        .replace(/&lt;/g, '<')
        .replace(/&gt;/g, '>')
        .replace(/&quot;/g, '"')
        .replace(/&#x27;/g, "'")
        .replace(/&#39;/g, "'")
        .replace(/&nbsp;/g, ' ');
      return text.replace(/\s+/g, ' ').trim();
    },
  },

  {
    name: 'html_sanitize',
    displayName: 'HTML Sanitize',
    description: 'Remove dangerous tags (script, style, iframe, etc.)',
    category: 'html',
    inputType: 'string',
    outputType: 'string',
    params: [],
    transform(input) {
      let html = String(input);
      // Remove dangerous tags and their content
      const dangerousTags = ['script', 'style', 'iframe', 'object', 'embed', 'frame', 'frameset', 'meta', 'link'];
      for (const tag of dangerousTags) {
        html = html.replace(new RegExp(`<${tag}\\b[^>]*>[\\s\\S]*?<\\/${tag}>`, 'gi'), '');
        html = html.replace(new RegExp(`<${tag}\\b[^>]*\\/?>`, 'gi'), '');
      }
      // Remove on* event attributes
      html = html.replace(/\s+on\w+\s*=\s*(?:"[^"]*"|'[^']*'|[^\s>]+)/gi, '');
      // Remove javascript: URLs in href/src/action
      html = html.replace(/(href|src|action)\s*=\s*(?:"javascript:[^"]*"|'javascript:[^']*')/gi, '');
      return html;
    },
  },

  {
    name: 'link_extraction',
    displayName: 'Extract Links',
    description: 'Extract all href URLs from anchor tags',
    category: 'html',
    inputType: 'string',
    outputType: 'array',
    params: [],
    transform(input) {
      const links = [];
      const re = /<a\s[^>]*href\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+))[^>]*>/gi;
      let match;
      while ((match = re.exec(input)) !== null) {
        links.push(match[1] || match[2] || match[3]);
      }
      return links;
    },
  },

  {
    name: 'extract_domain',
    displayName: 'Extract Domain',
    description: 'Extract domain from URL',
    category: 'html',
    inputType: 'string',
    outputType: 'string',
    params: [],
    transform(input) {
      try {
        // Handle protocol-relative URLs
        const url = input.startsWith('//') ? `https:${input}` : input;
        return new URL(url).hostname;
      } catch {
        // Regex fallback
        const match = /^(?:https?:)?\/\/([^/:?#]+)/.exec(input);
        return match ? match[1] : '';
      }
    },
  },

  {
    name: 'resolve_url',
    displayName: 'Resolve URL',
    description: 'Resolve relative URL against a base',
    category: 'html',
    inputType: 'string',
    outputType: 'string',
    params: [
      { name: 'base_url', type: 'string', default: '', description: 'Base URL' },
    ],
    transform(input, { base_url = '' } = {}) {
      if (!base_url) return input;
      try {
        return new URL(input, base_url).href;
      } catch {
        return input;
      }
    },
  },
];
