export function calcProgress(currentDoc, resultDoc, maxDist, dmp) {
    const diffs = dmp.diff_main(currentDoc, resultDoc);
    const dist = dmp.diff_levenshtein(diffs);
    return Math.max(0, Math.floor((maxDist - dist) / maxDist * 100));
}

export function getCarPosition(progress) {
    return `${progress}%`;
}