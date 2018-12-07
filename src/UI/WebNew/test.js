function Welcome(props){
    return <div>Hi {props.name}</div>;
}

function App() {
  return (
    <div>
      <Welcome name="Sara" />
      <Welcome name="Cahal" />
      <Welcome name="Edite" />
    </div>
  );
}

 ReactDOM.render(
  <App />,
  document.getElementById('root')
);