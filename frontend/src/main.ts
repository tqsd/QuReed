import App from './App.svelte';
import './styles.css';
import { mount } from 'svelte';

document.documentElement.classList.add('dark');

const app = mount(App, {
  target: document.getElementById('app') as HTMLElement
});

export default app;
