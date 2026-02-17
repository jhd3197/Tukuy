/**
 * Tukuy Date Transformers — JS port
 *
 * Ports of tukuy/plugins/date Python transformers.
 * Uses native Date API.
 */

/**
 * Parse a date string with a strftime-style format.
 * Supports common codes: %Y, %m, %d, %H, %M, %S.
 */
function parseDateString(str, format) {
  const tokens = {
    '%Y': '(?<Y>\\d{4})',
    '%m': '(?<m>\\d{2})',
    '%d': '(?<d>\\d{2})',
    '%H': '(?<H>\\d{2})',
    '%M': '(?<M>\\d{2})',
    '%S': '(?<S>\\d{2})',
  };

  let pattern = format.replace(/[-/\\^$*+?.()|[\]{}]/g, '\\$&');
  for (const [tok, re] of Object.entries(tokens)) {
    pattern = pattern.replace(tok.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), re);
  }

  const match = new RegExp(`^${pattern}$`).exec(str);
  if (!match) throw new Error(`Date '${str}' doesn't match format '${format}'`);

  const g = match.groups || {};
  return new Date(
    parseInt(g.Y || '1970', 10),
    parseInt(g.m || '1', 10) - 1,
    parseInt(g.d || '1', 10),
    parseInt(g.H || '0', 10),
    parseInt(g.M || '0', 10),
    parseInt(g.S || '0', 10),
  );
}

export const dateTransformers = [
  {
    name: 'date',
    displayName: 'Parse Date',
    description: 'Parse date string to ISO format',
    category: 'date',
    inputType: 'string',
    outputType: 'string',
    params: [
      { name: 'format', type: 'string', default: '%Y-%m-%d', description: 'Date format (strftime codes)' },
    ],
    transform(input, { format = '%Y-%m-%d' } = {}) {
      const d = parseDateString(input, format);
      return d.toISOString();
    },
  },

  {
    name: 'duration_calc',
    displayName: 'Duration Calculator',
    description: 'Calculate duration between dates',
    category: 'date',
    inputType: 'string',
    outputType: 'number',
    params: [
      { name: 'unit', type: 'string', default: 'days', description: 'Unit', options: ['days', 'months', 'years'] },
      { name: 'format', type: 'string', default: '%Y-%m-%d', description: 'Date format' },
      { name: 'end', type: 'string', default: null, description: 'End date (null = today)' },
    ],
    transform(input, { unit = 'days', format = '%Y-%m-%d', end = null } = {}) {
      const startDate = parseDateString(input, format);
      const endDate = end ? parseDateString(end, format) : new Date();

      if (unit === 'days') {
        const msPerDay = 86400000;
        const startUTC = Date.UTC(startDate.getFullYear(), startDate.getMonth(), startDate.getDate());
        const endUTC = Date.UTC(endDate.getFullYear(), endDate.getMonth(), endDate.getDate());
        return Math.round((endUTC - startUTC) / msPerDay);
      } else if (unit === 'months') {
        return (endDate.getFullYear() - startDate.getFullYear()) * 12
          + endDate.getMonth() - startDate.getMonth();
      } else if (unit === 'years') {
        return endDate.getFullYear() - startDate.getFullYear();
      }
      throw new Error(`Invalid unit: ${unit}`);
    },
  },

  {
    name: 'age_calc',
    displayName: 'Age Calculator',
    description: 'Calculate age in years from birth date',
    category: 'date',
    inputType: 'string',
    outputType: 'number',
    params: [
      { name: 'reference_date', type: 'string', default: null, description: 'Reference date (null = today)' },
    ],
    transform(input, { reference_date = null } = {}) {
      const birth = parseDateString(input, '%Y-%m-%d');
      const ref = reference_date ? parseDateString(reference_date, '%Y-%m-%d') : new Date();

      let years = ref.getFullYear() - birth.getFullYear();
      const refMonth = ref.getMonth(), refDay = ref.getDate();
      const birthMonth = birth.getMonth(), birthDay = birth.getDate();

      if (refMonth < birthMonth || (refMonth === birthMonth && refDay < birthDay)) {
        years -= 1;
      }
      return years;
    },
  },
];
