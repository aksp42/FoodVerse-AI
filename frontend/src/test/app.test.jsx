import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect } from 'vitest';
import App from '../App';
import { AuthProvider } from '../context/AuthContext';
import { AppDataProvider } from '../context/AppDataContext';
import { ToastProvider } from '../context/ToastContext';

function renderApp(path = '/') {
  return render(
    <MemoryRouter initialEntries={[path]} future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <ToastProvider><AuthProvider><AppDataProvider><App /></AppDataProvider></AuthProvider></ToastProvider>
    </MemoryRouter>,
  );
}

async function loginDemo(path = '/login') {
  const user = userEvent.setup();
  renderApp(path);
  await user.click(await screen.findByRole('button', { name: /continue with demo account/i }));
  await screen.findByRole('navigation', { name: /primary/i }, { timeout: 4000 });
  return user;
}

describe('Food Verse AI', () => {
  it('renders the landing page with CTA', async () => {
    renderApp('/');
    expect(await screen.findByRole('heading', { level: 1, name: /smarter food/i })).toBeInTheDocument();
    expect(screen.getAllByRole('link', { name: /get started/i }).length).toBeGreaterThan(0);
  });

  it('protects app routes', async () => {
    renderApp('/app/food');
    expect(await screen.findByRole('heading', { name: /welcome back/i })).toBeInTheDocument();
  });

  it('validates login and signup forms', async () => {
    const user = userEvent.setup();
    renderApp('/login');
    await user.click(await screen.findByRole('button', { name: /^log in$/i }));
    expect(await screen.findByText(/email is required/i)).toBeInTheDocument();
    expect(screen.getByText(/password is required/i)).toBeInTheDocument();
  });

  it('navigates back to the landing page from auth via the back button', async () => {
    const user = userEvent.setup();
    renderApp('/login');
    const backBtn = await screen.findByRole('link', { name: /back to home/i });
    expect(backBtn).toBeInTheDocument();
    await user.click(backBtn);
    expect(await screen.findByRole('heading', { level: 1, name: /smarter food/i })).toBeInTheDocument();
  });

  it('validates the signup form', async () => {
    const user = userEvent.setup();
    renderApp('/signup');
    await user.click(await screen.findByRole('button', { name: /create account/i }));
    expect(await screen.findByText(/name is required/i)).toBeInTheDocument();
    expect(screen.getByText(/please accept the terms/i)).toBeInTheDocument();
  });

  it('logs in with demo account and shows icon-only nav with 7 labelled links', async () => {
    await loginDemo();
    expect(await screen.findByText(/your smart food companion/i, {}, { timeout: 4000 })).toBeInTheDocument();
    const nav = screen.getByRole('navigation', { name: /primary/i });
    expect(within(nav).getAllByRole('link')).toHaveLength(7);
    expect(within(nav).getByRole('link', { name: /meal planner/i })).toBeInTheDocument();
  });

  it('visits every page from the nav', async () => {
    const user = await loginDemo();
    const nav = screen.getByRole('navigation', { name: /primary/i });
    const pages = [
      ['Food Recognition', /food recognition/i],
      ['Freshness Detection', /freshness & spoilage/i],
      ['Hygiene Monitor', /restaurant hygiene|hygiene & kitchen/i],
      ['Cooking Assistant', /smart cooking assistant/i],
      ['Meal Planner', /personalized meal planner/i],
      ['Profile & Settings', /profile & settings/i],
    ];
    for (const [label, heading] of pages) {
      await user.click(within(nav).getByRole('link', { name: label }));
      expect(await screen.findByRole('heading', { level: 1, name: heading })).toBeInTheDocument();
    }
  });

  it('shows the food recognition page with predict button and empty state', async () => {
    const user = await loginDemo('/login');
    await user.click(within(screen.getByRole('navigation', { name: /primary/i })).getByRole('link', { name: 'Food Recognition' }));
    expect(await screen.findByRole('heading', { level: 1, name: /food recognition/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /analyze food & nutrition/i })).toBeInTheDocument();
    expect(screen.getByText(/nothing analyzed yet/i)).toBeInTheDocument();
  });

  it('manages ingredients in the cooking assistant', async () => {
    const user = await loginDemo();
    await user.click(within(screen.getByRole('navigation', { name: /primary/i })).getByRole('link', { name: 'Cooking Assistant' }));
    const input = await screen.findByLabelText(/add ingredient/i);
    await user.type(input, 'spinach{enter}');
    expect(await screen.findByRole('button', { name: /remove spinach/i })).toBeInTheDocument();
    await user.type(input, 'spinach{enter}');
    expect(await screen.findByText(/already in your list/i)).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: /remove spinach/i }));
    expect(screen.queryByRole('button', { name: /remove spinach/i })).not.toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: /view full recipe/i }));
    expect(await screen.findByRole('dialog')).toBeInTheDocument();
  });

  it('generates a meal plan', async () => {
    const user = await loginDemo();
    await user.click(within(screen.getByRole('navigation', { name: /primary/i })).getByRole('link', { name: 'Meal Planner' }));
    expect(await screen.findByRole('table', {}, { timeout: 3000 })).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: /regenerate plan/i }));
    await waitFor(() => expect(screen.getByRole('button', { name: /regenerate plan/i })).toBeEnabled(), { timeout: 4000 });
    const cells = screen.getAllByRole('button', { name: /mon breakfast/i });
    await user.click(cells[0]);
    expect(await screen.findByRole('dialog')).toBeInTheDocument();
  });

  it('validates profile edits', async () => {
    const user = await loginDemo();
    await user.click(within(screen.getByRole('navigation', { name: /primary/i })).getByRole('link', { name: 'Profile & Settings' }));
    await user.click(await screen.findByRole('button', { name: /edit profile/i }));
    const name = screen.getByLabelText(/full name/i);
    await user.clear(name);
    await user.click(screen.getByRole('button', { name: /save changes/i }));
    expect(await screen.findByText(/name is required/i)).toBeInTheDocument();
    await user.type(name, 'Akanksha Singh');
    await user.click(screen.getByRole('button', { name: /save changes/i }));
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
    expect(screen.getByRole('heading', { name: 'Akanksha Singh' })).toBeInTheDocument();
  });

  it('handles image upload: rejects non-images, previews and analyzes images', async () => {
    const user = await loginDemo();
    await user.click(within(screen.getByRole('navigation', { name: /primary/i })).getByRole('link', { name: 'Freshness Detection' }));
    await screen.findByRole('heading', { level: 1, name: /freshness & spoilage/i });
    const input = document.querySelector('input[type="file"]');
    await userEvent.setup({ applyAccept: false }).upload(input, new File(['hello'], 'notes.txt', { type: 'text/plain' }));
    expect(await screen.findByText(/please choose an image file/i)).toBeInTheDocument();
    await user.upload(input, new File(['img_content'], 'tomato.png', { type: 'image/png' }));
    expect(await screen.findByAltText(/selected upload preview/i)).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: /analyze freshness/i }));
    expect(await screen.findByRole('heading', { level: 3, name: /freshness & spoilage assessment/i })).toBeInTheDocument();
  });

  it('shows 404 for unknown routes', async () => {
    renderApp('/nope');
    expect(await screen.findByText(/isn't on the menu/i)).toBeInTheDocument();
  });
});
