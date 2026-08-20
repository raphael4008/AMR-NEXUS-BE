const [reference, setReference] = useState(null);
const checkReference = async (pathogen, antibiotic) => {
  const res = await fetch(`https://api.clsi.org/breakpoints?pathogen=${pathogen}&abx=${antibiotic}`);
  const data = await res.json();
  setReference(data);
};