import { useEffect, useState } from "react";

const KIND_LABELS = { 0: "Kind A", 1: "Kind B", 2: "Kind C" };

function studentCount(count) {
  return count + (count === 1 ? " student" : " students");
}

function mixText(counts) {
  return ["0", "1", "2"]
    .map((key) => KIND_LABELS[key] + " " + counts[key])
    .join(" · ");
}

function missingKind(counts) {
  return ["0", "1", "2"].some((key) => counts[key] === 0);
}

export default function App() {
  const [names, setNames] = useState([]);
  const [nGroups, setNGroups] = useState(8);
  const [groups, setGroups] = useState(null);

  useEffect(() => {
    fetch("/api/students")
      .then((response) => response.json())
      .then(setNames);
  }, []);

  useEffect(() => {
    fetch("/api/groups?n_groups=" + nGroups)
      .then((response) => response.json())
      .then(setGroups);
  }, [nGroups]);

  function changeGroupCount(event) {
    const value = Number(event.target.value);
    if (value >= 1 && value <= 30) setNGroups(value);
  }

  return (
    <main>
      <ul id="names">
        {names.map((name) => (
          <li key={name}>{name}</li>
        ))}
      </ul>
      <h1>Class groups</h1>
      <label className="group-count">
        Number of groups
        <input
          type="number"
          name="n_groups"
          min={1}
          max={30}
          value={nGroups}
          onChange={changeGroupCount}
        />
      </label>
      <p className="summary">
        {groups
          ? groups.n_groups +
            " groups, " +
            groups.groups_missing_a_cluster +
            " missing a kind of student."
          : ""}
      </p>
      <div className="groups">
        {groups &&
          groups.groups.map((group) => (
            <article
              key={group.group}
              className={missingKind(group.cluster_counts) ? "missing" : undefined}
            >
              <h2>Group {group.group}</h2>
              <p className="count">{studentCount(group.members.length)}</p>
              <ul className="roster">
                {group.members.map((name) => (
                  <li key={name}>
                    <span>{name}</span>
                    <span className="group-no">{group.group}</span>
                  </li>
                ))}
              </ul>
              <p className="mix">{mixText(group.cluster_counts)}</p>
            </article>
          ))}
      </div>
    </main>
  );
}
