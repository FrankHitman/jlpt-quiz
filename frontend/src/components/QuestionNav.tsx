interface Props {
  total: number;
  current: number;
  answered: boolean[];
  flagged: boolean[];
  onJump: (index: number) => void;
}

export function QuestionNav({ total, current, answered, flagged, onJump }: Props) {
  return (
    <div className="qnav">
      <div className="qnav-title">題號</div>
      <div className="qnav-grid">
        {Array.from({ length: total }, (_, i) => {
          let cls = 'qnav-item';
          if (i === current) cls += ' current';
          else if (flagged[i]) cls += ' flagged';
          else if (answered[i]) cls += ' answered';
          return (
            <button key={i} type="button" className={cls} onClick={() => onJump(i)} aria-label={`第 ${i + 1} 題`}>
              {i + 1}
            </button>
          );
        })}
      </div>
      <div className="qnav-legend">
        <span>
          <i className="dot dot-answered" />
          已答
        </span>
        <span>
          <i className="dot dot-flagged" />
          待定
        </span>
        <span>
          <i className="dot dot-todo" />
          未答
        </span>
      </div>
    </div>
  );
}
