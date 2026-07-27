import { calcProgress, getCarPosition } from '../frontend/js/game.js';

test('progress is 0 when doc is unchanged', () => {
    // mock dmp
    const dmp = {
        diff_main: () => [],
        diff_levenshtein: () => 10
    };
    expect(calcProgress('start', 'result', 10, dmp)).toBe(0);
});

test('progress is 100 when doc matches result', () => {
    const dmp = {
        diff_main: () => [],
        diff_levenshtein: () => 0
    };
    expect(calcProgress('result', 'result', 10, dmp)).toBe(100);
});

test('car position returns correct percentage string', () => {
    expect(getCarPosition(50)).toBe('50%');
    expect(getCarPosition(0)).toBe('0%');
    expect(getCarPosition(100)).toBe('100%');
});