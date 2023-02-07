import logo from './logo.svg';
import './App.css';
import { useState, useRef } from 'react';

function App() {
  // fetches JSON data passed in by flask.render_template and loaded
  // in public/index.html in the script with id "data"
  const args = JSON.parse(document.getElementById('data').text);
  const [artistIDs, setArtistIDs] = useState(args.artist_ids);

  const handleSubmit = (e) => {
    e.preventDefault();

    if (e.target['addButton']) {
      fetch('/addArtist', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
        },

        body: JSON.stringify({ artist_id: e.target['artistText'].value }),
      })
        .then((response) => response.json())
        .then((data) => {
          console.log('hi ' + data);
          setArtistIDs((artistIDs) => [...artistIDs, data.aritst_ID_server]);
        });
    }

    if (e.target['deleteButton']) {
      fetch('/deleteArtist', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
        },

        body: JSON.stringify({ artist_id: e.target['artistText'].value }),
      })
        .then((response) => response.json())
        .then((data) => {
          console.log(data);
          setArtistIDs((artistIDs) => [...artistIDs, data.aritst_IDs_server]);
        });
    }
  };

  function onSave() {
    window.location.href = '/index';
  }

  let has_artists_saved = false;
  return (
    <>
      <h1>{args.current_user}'s Song Explorer</h1>
      {args.has_artists_saved ? (
        <>
          <h2>{args.song_name}</h2>
          <h3>{args.song_artist}</h3>
          <div>
            <img src={args.song_image_url} width={300} height={300} />
          </div>
          <div>
            <audio controls>
              <source src={args.preview_url} />
            </audio>
          </div>
          <a href={args.genius_url}> Click here to see lyrics! </a>
          <div>
            <h2>Your saved Artists:</h2>
            {artistIDs.map((artistIDs) => (
              <p>{artistIDs}</p>
            ))}
          </div>
        </>
      ) : (
        <h2>Looks like you don't have anything saved! Use the form below!</h2>
      )}
      <h2>Save a favorite artist ID for later:</h2>
      <form onSubmit={handleSubmit} method="POST" id="artist">
        <input type="text" name="artistText" />
        <input type="submit" name="addButton" value="Add" />
        <input type="submit" name="deleteButton" value="Delete" />
      </form>
      <button onClick={onSave}>Save</button>
    </>
  );
}

export default App;
