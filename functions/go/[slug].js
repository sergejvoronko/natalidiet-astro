import links from '../../src/data/go-links.json';

const BOT = /bot|crawl|spider|slurp|preview|facebookexternalhit|embedly|headless|lighthouse|monitor|curl|wget|python|go-http|okhttp/i;

export async function onRequest({ request, params, env, next }) {
  const link = links[params.slug];
  // Unknown slug: fall through to the static 404, same as before this Function existed.
  if (!link) return next();

  if (request.method === 'GET' && env.GO_CLICKS) {
    const ua = request.headers.get('user-agent') || '';
    let from = '';
    try {
      const ref = new URL(request.headers.get('referer') || '');
      from = /(^|\.)(natalidiet\.eu|natalidiet-astro\.pages\.dev)$/.test(ref.hostname) ? ref.pathname : `ext:${ref.hostname}`;
    } catch {}
    env.GO_CLICKS.writeDataPoint({
      blobs: [params.slug, from, BOT.test(ua) ? 'bot' : 'human', request.cf?.country || '', /mobi/i.test(ua) ? 'mobile' : 'desktop'],
      doubles: [1],
      indexes: [params.slug],
    });
  }

  return new Response(null, {
    status: link.status,
    headers: {
      Location: link.url,
      'X-Robots-Tag': 'noindex, nofollow',
      'Cache-Control': 'private, no-store',
    },
  });
}
