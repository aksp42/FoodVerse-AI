import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import FoodRecognition from '../pages/FoodRecognition';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider } from '../context/AuthContext';
import { AppDataProvider } from '../context/AppDataContext';
import { ToastProvider } from '../context/ToastContext';

function renderPage() {
  return render(
    <MemoryRouter>
      <AuthProvider>
        <ToastProvider>
          <AppDataProvider>
            <FoodRecognition />
          </AppDataProvider>
        </ToastProvider>
      </AuthProvider>
    </MemoryRouter>
  );
}

describe('FoodRecognition Component — Smart Bridge Activity 2.1', () => {
  it('renders initial state with empty prompt and Gemini info card', () => {
    renderPage();
    expect(screen.getByRole('heading', { level: 1, name: /food recognition/i })).toBeInTheDocument();
    expect(screen.getByText(/nothing analyzed yet/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /analyze food & nutrition/i })).toBeDisabled();
  });

  it('handles image selection, analysis, and renders food prediction with OpenCV badge and nutrition', async () => {
    renderPage();

    vi.spyOn(globalThis, 'fetch').mockImplementation(async (url) => {
      if (String(url).includes('/api/predict')) {
        return {
          ok: true,
          json: async () => ({
            success: true,
            is_food: true,
            food_name: 'Chole Bhature',
            predicted_class: 'Chole Bhature',
            confidence: 'High',
            certainty: 'High',
            description: 'Authentic spiced chickpea curry with deep fried bhature.',
            food_items: ['Bhatura', 'Chickpeas', 'Pickled onions'],
            visual_observations: ['Puffed golden brown bhatura', 'Rich dark gravy'],
            nutrition: {
              serving: '1 plate (approx 250g)',
              calories: 620,
              protein: 16,
              carbs: 78,
              fat: 24,
              tip: 'Enjoy with cucumber raita for digestive balance.'
            },
            preprocessing_applied: {
              original_dimensions: [1200, 900],
              processed_dimensions: [1200, 900],
              resized: false,
              color_space: 'RGB',
              engine: 'OpenCV 4.14.0'
            },
            engine: 'gemini-3.5-flash-lite Vision (Multimodal AI)'
          })
        };
      }
      return { ok: true, json: async () => ({ status: 'ok' }) };
    });

    const input = document.querySelector('input[type="file"]');
    const fakeFile = new File(['food_bytes'], 'chole.jpg', { type: 'image/jpeg' });
    fireEvent.change(input, { target: { files: [fakeFile] } });

    const analyzeBtn = screen.getByRole('button', { name: /analyze food & nutrition/i });
    expect(analyzeBtn).toBeEnabled();
    fireEvent.click(analyzeBtn);

    // Verify prediction rendered
    expect(await screen.findByRole('heading', { level: 2, name: /chole bhature/i })).toBeInTheDocument();
    expect(screen.getByText(/authentic spiced chickpea curry/i)).toBeInTheDocument();
    expect(screen.getByText(/opencv 1200×900/i)).toBeInTheDocument();
    expect(screen.getByText(/620/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /download nutrition report/i })).toBeInTheDocument();

    // Verify reset
    const resetBtn = screen.getByRole('button', { name: /analyze another image/i });
    fireEvent.click(resetBtn);
    expect(screen.getByText(/nothing analyzed yet/i)).toBeInTheDocument();
  });

  it('renders non-food warning banner when an uploaded image is non-food', async () => {
    renderPage();

    vi.spyOn(globalThis, 'fetch').mockImplementation(async (url) => {
      if (String(url).includes('/api/predict')) {
        return {
          ok: true,
          json: async () => ({
            success: true,
            is_food: false,
            food_name: 'Unrecognized Non-Food Object',
            predicted_class: 'Unrecognized Non-Food Object',
            confidence: 'Low',
            certainty: 'Low',
            description: 'Photograph displays an office workspace with no edible items.',
            food_items: [],
            visual_observations: ['Computer keyboard and desk detected'],
            nutrition: null,
            preprocessing_applied: {
              original_dimensions: [800, 600],
              processed_dimensions: [800, 600],
              resized: false,
              color_space: 'RGB',
              engine: 'OpenCV 4.14.0'
            },
            engine: 'gemini-3.5-flash-lite Vision (Multimodal AI)'
          })
        };
      }
      return { ok: true, json: async () => ({ status: 'ok' }) };
    });

    const input = document.querySelector('input[type="file"]');
    const fakeFile = new File(['desk_bytes'], 'desk.jpg', { type: 'image/jpeg' });
    fireEvent.change(input, { target: { files: [fakeFile] } });

    const analyzeBtn = screen.getByRole('button', { name: /analyze food & nutrition/i });
    expect(analyzeBtn).toBeEnabled();
    fireEvent.click(analyzeBtn);

    const nonFoodNotices = await screen.findAllByText(/non-food or ambiguous image detected/i);
    expect(nonFoodNotices.length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/photograph displays an office workspace/i)).toBeInTheDocument();
    expect(screen.queryByText(/estimated nutritional profile/i)).not.toBeInTheDocument();
  });

  it('renders Activity 2.2 health score, dietary fiber, data source, and insights', async () => {
    renderPage();

    vi.spyOn(globalThis, 'fetch').mockImplementation(async (url) => {
      if (String(url).includes('/api/predict')) {
        return {
          ok: true,
          json: async () => ({
            success: true,
            is_food: true,
            food_name: 'Palak Paneer',
            predicted_class: 'Palak Paneer',
            confidence: 'High',
            certainty: 'High',
            description: 'Nutritious cottage cheese cubes in spiced spinach puree.',
            food_items: ['Spinach', 'Paneer'],
            visual_observations: ['Deep green pureed spinach', 'Fresh seared paneer'],
            nutrition: {
              status: 'available',
              calories: 290,
              protein: 15.5,
              carbs: 12.0,
              fat: 20.0,
              fiber: 5.8,
              serving: '1 bowl (~230g spinach gravy with paneer)',
              health_score: 70,
              health_score_label: 'Balanced Meal',
              health_score_breakdown: [
                '+15 pts: High protein content (15.5g supports satiety & muscle maintenance)',
                '+10 pts: Good dietary fiber content (5.8g)',
                '-15 pts: Very high lipid concentration (62.1% calories from fat, typical of deep frying)'
              ],
              data_source: 'ICMR-NIN Indian Food Composition Tables (IFCT 2017)',
              estimation_method: 'reference_standard',
              uncertainty_note: 'Values derived from verified food composition reference tables.',
              insights: [
                'Rich Protein Source: Provides 15.5g of protein.',
                'Fiber-Rich: Delivers 5.8g dietary fiber.'
              ]
            },
            preprocessing_applied: {
              processed_dimensions: [800, 600],
              engine: 'OpenCV 4.14.0'
            },
            engine: 'gemini-3.5-flash-lite Vision (Multimodal AI)'
          })
        };
      }
      return { ok: true, json: async () => ({ status: 'ok' }) };
    });

    const input = document.querySelector('input[type="file"]');
    const fakeFile = new File(['spinach_bytes'], 'palak.jpg', { type: 'image/jpeg' });
    fireEvent.change(input, { target: { files: [fakeFile] } });

    const analyzeBtn = screen.getByRole('button', { name: /analyze food & nutrition/i });
    fireEvent.click(analyzeBtn);

    expect(await screen.findByRole('heading', { level: 2, name: /palak paneer/i })).toBeInTheDocument();
    expect(screen.getByText(/nutritional balance score/i)).toBeInTheDocument();
    expect(screen.getByText(/70 \/ 100 • balanced meal/i)).toBeInTheDocument();
    expect(screen.getByText(/source: icmr-nin indian food composition tables/i)).toBeInTheDocument();
    expect(screen.getAllByText(/5.8g/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/fiber-rich: delivers 5.8g dietary fiber/i)).toBeInTheDocument();
  });

  it('renders honest insufficient data state when nutrition data is incomplete', async () => {
    renderPage();

    vi.spyOn(globalThis, 'fetch').mockImplementation(async (url) => {
      if (String(url).includes('/api/predict')) {
        return {
          ok: true,
          json: async () => ({
            success: true,
            is_food: true,
            food_name: 'Unknown Mixed Broth',
            predicted_class: 'Unknown Mixed Broth',
            confidence: 'Low',
            certainty: 'Low',
            description: 'Unidentified broth with obscured contents.',
            food_items: [],
            visual_observations: [],
            nutrition: {
              status: 'insufficient_data',
              message: 'Nutritional reference unavailable and visual estimation was insufficient.',
              calories: null,
              protein: null,
              carbs: null,
              fat: null,
              fiber: null,
              serving: 'Unknown portion',
              health_score: null,
              health_score_label: 'Insufficient Data'
            },
            preprocessing_applied: {
              processed_dimensions: [640, 480],
              engine: 'OpenCV 4.14.0'
            },
            engine: 'gemini-3.5-flash-lite Vision (Multimodal AI)'
          })
        };
      }
      return { ok: true, json: async () => ({ status: 'ok' }) };
    });

    const input = document.querySelector('input[type="file"]');
    const fakeFile = new File(['broth_bytes'], 'broth.jpg', { type: 'image/jpeg' });
    fireEvent.change(input, { target: { files: [fakeFile] } });

    const analyzeBtn = screen.getByRole('button', { name: /analyze food & nutrition/i });
    fireEvent.click(analyzeBtn);

    expect(await screen.findByText(/insufficient reference data/i)).toBeInTheDocument();
    expect(screen.getByText(/nutritional reference unavailable and visual estimation was insufficient/i)).toBeInTheDocument();
  });
});
