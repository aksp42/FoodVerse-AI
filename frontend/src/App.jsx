import { lazy, Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import AppLayout from './components/AppLayout';
import { ProtectedRoute, PublicOnlyRoute } from './components/RouteGuards';
import { ErrorBoundary, PageLoader } from './components/Feedback';

const Landing = lazy(() => import('./pages/Landing'));
const Login = lazy(() => import('./pages/Auth').then((m) => ({ default: m.Login })));
const Signup = lazy(() => import('./pages/Auth').then((m) => ({ default: m.Signup })));
const Dashboard = lazy(() => import('./pages/Dashboard'));
const FoodRecognition = lazy(() => import('./pages/FoodRecognition'));
const Freshness = lazy(() => import('./pages/Freshness'));
const Hygiene = lazy(() => import('./pages/Hygiene'));
const Cooking = lazy(() => import('./pages/Cooking'));
const MealPlanner = lazy(() => import('./pages/MealPlanner'));
const Profile = lazy(() => import('./pages/Profile'));
const NotFound = lazy(() => import('./pages/NotFound'));

export default function App() {
  return (
    <ErrorBoundary>
      <Suspense fallback={<PageLoader />}>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<PublicOnlyRoute><Login /></PublicOnlyRoute>} />
          <Route path="/signup" element={<PublicOnlyRoute><Signup /></PublicOnlyRoute>} />

          {/* Canonical Milestone 6 Route Aliases (from Project Architecture) */}
          <Route path="/dashboard" element={<Navigate to="/app" replace />} />
          <Route path="/food-recognition" element={<Navigate to="/app/food" replace />} />
          <Route path="/freshness-detector" element={<Navigate to="/app/freshness" replace />} />
          <Route path="/hygiene-monitor" element={<Navigate to="/app/hygiene" replace />} />
          <Route path="/kitchen-assistant" element={<Navigate to="/app/cooking" replace />} />
          <Route path="/meal-planner" element={<Navigate to="/app/meal-planner" replace />} />

          <Route path="/app" element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
            <Route index element={<Dashboard />} />
            <Route path="food" element={<FoodRecognition />} />
            <Route path="food-recognition" element={<FoodRecognition />} />
            <Route path="freshness" element={<Freshness />} />
            <Route path="freshness-detector" element={<Freshness />} />
            <Route path="hygiene" element={<Hygiene />} />
            <Route path="hygiene-monitor" element={<Hygiene />} />
            <Route path="cooking" element={<Cooking />} />
            <Route path="kitchen-assistant" element={<Cooking />} />
            <Route path="meal-planner" element={<MealPlanner />} />
            <Route path="profile" element={<Profile />} />
            <Route path="*" element={<NotFound inApp />} />
          </Route>

          <Route path="*" element={<NotFound />} />
        </Routes>
      </Suspense>
    </ErrorBoundary>
  );
}
