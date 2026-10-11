export function formatSeconds(total: number): string {
  const s = Math.max(0, Math.floor(total));
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  const mm = h > 0 ? String(m).padStart(2, '0') : String(m);
  return `${h > 0 ? `${h}:` : ''}${mm}:${String(sec).padStart(2, '0')}`;
}

/** 純展示型倒計時；到點自動提交由父組件負責。 */
export function Timer({ secondsLeft }: { secondsLeft: number }) {
  const danger = secondsLeft <= 600;
  return (
    <div className={danger ? 'timer timer-danger' : 'timer'} title="剩餘時間">
      ⏱ {formatSeconds(secondsLeft)}
    </div>
  );
}
