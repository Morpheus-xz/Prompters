/** Browser entry point; wiring only, with no business or rendering logic. */
import { actions } from './actions.js';
import { PlannerApp } from './application.js';

void new PlannerApp(actions).start();
