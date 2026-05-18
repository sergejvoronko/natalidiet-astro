export async function onRequestPost({ request, env }) {
  try {
    const { name, email, subject, message, consent } = await request.json();

    if (!name?.trim() || !email?.trim() || !message?.trim() || !consent) {
      return json({ error: 'Missing required fields' }, 400);
    }
    if (!email.includes('@')) {
      return json({ error: 'Invalid email address' }, 400);
    }
    if (message.length > 3000) {
      return json({ error: 'Message too long' }, 400);
    }

    const res = await fetch('https://api.brevo.com/v3/smtp/email', {
      method: 'POST',
      headers: {
        'api-key': env.BREVO_API_KEY,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        sender: { name: 'Natali Diet', email: 'contact@natalidiet.eu' },
        to: [{ email: env.CONTACT_TO_EMAIL || 'contact@natalidiet.eu' }],
        replyTo: { email: email.trim() },
        subject: subject?.trim()
          ? `[Contact] ${subject.trim()}`
          : `[Contact] Message from ${name.trim()}`,
        textContent: `Name: ${name}\nEmail: ${email}\n\n${message}`,
        htmlContent: `
          <p><strong>Name:</strong> ${esc(name)}</p>
          <p><strong>Email:</strong> ${esc(email)}</p>
          ${subject ? `<p><strong>Subject:</strong> ${esc(subject)}</p>` : ''}
          <p><strong>Message:</strong></p>
          <p style="white-space:pre-wrap">${esc(message)}</p>
        `,
      }),
    });

    if (!res.ok) {
      console.error('Brevo error:', await res.text());
      return json({ error: 'Failed to send' }, 500);
    }

    return json({ ok: true }, 200);
  } catch (e) {
    console.error('Contact handler error:', e);
    return json({ error: 'Server error' }, 500);
  }
}

function json(data, status) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

function esc(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}
